import os
import sys
import socket
import select
import pickle
from collections import defaultdict
from utils.utils import Interface, RouteTable, DataFrame, ARP, Hosts, PQ

class Station:
    def __init__(self, params):
        self.isroute = True if "route" in params[1] else False
        self.iface = self.read_file(params[2])
        self.rtable = self.read_file(params[3])
        self.name = list(self.iface.keys())
        self.hosts = Hosts(params[4]).get_hosts()
        self.arp = ARP()
        self.pq = PQ()
        self.iface2fd = {}
        self.fd2iface = {}
        self.ip2fd = {}
        
    def print_details(self):
        print("""[DEBUG] Station details:
            name \t- {}
            iface_path \t- {}
            rtable_path \t\t- {}
            isrouter \t- {}
            """.format(self.name, self.iface, self.rtable, self.isroute))
     
    def get_landetails(self, lanname):
        with open("./symlinks/.{}.addr".format(lanname)) as file:
                ip = file.read()
        with open("./symlinks/.{}.port".format(lanname)) as file:
            port = file.read()         
        return ip, port
    
    def get_key(self, val):
        for key, value in self.hosts.items():
            if val == value:
                return key
        return None

    def initialize(self):
        client_set = set()
        client_set.add(sys.stdin)
        for iface_name in self.iface:
            print("[INFO] Initializing interface ", iface_name)
            cur_iface = self.iface[iface_name]
            bridge_ip, port = self.get_landetails(cur_iface.lanname)
            
            hints = socket.getaddrinfo(bridge_ip, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
            addr = None
            for addr in hints:
                try:
                    sockfd = socket.socket(addr[0], addr[1], addr[2])
                    station_ip = self.hosts[iface_name]
                    print("station => ", iface_name, station_ip)
                    sockfd.connect(addr[4])
                    self.iface2fd[iface_name] = sockfd
                    self.fd2iface[sockfd] = iface_name
                    self.ip2fd[station_ip] = sockfd
                    break
                except socket.error:
                    if sockfd:
                        sockfd.close()
                    sockfd = None

            if sockfd is None:
                print("Cannot connect")
                sys.exit(1)

            # Get active port and IP address
            addr_info = sockfd.getsockname()
            ipstr = addr_info[0]
            port = addr_info[1]
            print("Station: connected to bridge on '{}' at '{}' thru '{}'".format(ipstr, bridge_ip, port))
            client_set.add(sockfd)

        while True:
            temp_set, _, _ = select.select(client_set, [], [])
            for r in temp_set:
                if r in client_set and r!= sys.stdin:
                    # Read bridge response
                    try:
                        data_frame = r.recv(4096)
                    except Exception as e:
                        print("[ERROR]", e, r)
                        sys.exit(0)
                    cur_iface = self.fd2iface[r]
                    if not data_frame:
                        print("Bridge disconnected.")
                        sys.exit(0)
                    data = pickle.loads(data_frame)
                    # print("data loaded at ", cur_iface, " => ", data, "\n")
                    if data["type"] == "arp_request":
                        # for station in self.name:
                        if data["dest_ip"] == self.hosts[cur_iface]:
                            data["dest_mac"] = self.iface[cur_iface].mac
                            data["type"] = "arp_reply"
                            serialised_arp = pickle.dumps(data) 
                            print("[DEBUG] It's My IP sending back ARP response\n")
                            r.send(serialised_arp)
                    elif data["type"] == "arp_reply":
                        iface_name = self.get_key(data["src_ip"])
                        # print("------------------------",iface_name)
                        # print("\n********** In ARP reply\n",data, "\n pq \n", self.pq.table)
                        self.arp.table[data["dest_ip"]] = data["dest_mac"]
                        if data["src_ip"] in self.pq.table and msg:
                            # print("\n$$$$$$$$$$$$$msg", self.pq.table[data["src_ip"]])
                            data_frame = { "type": "dataframe", "data": self.encapsualte(self.pq.table[data["src_ip"]], data["src_ip"], data["src_mac"], data["dest_ip"], data["dest_mac"])}
                            self.pq.table[data["src_ip"]].pop(0)
                            serialised_data = pickle.dumps(data_frame)
                            self.ip2fd[data["src_ip"]].send(serialised_data)
                    elif data["data"].dll_dest_mac == self.iface[self.name[0]].mac:
                        data["data"].print_details()
                        print("{} >> {}".format(self.name[0], data["data"].msg))
                if r == sys.stdin:
                    # Write client input to the bridge
                    msg = sys.stdin.readline()
                    if not msg:
                        sys.exit(0)
                    msg_args = msg.split(" ", 2)
                    if msg_args[0] == "send":
                        msg_args = msg.split(" ", 3)
                        dest_host = msg.split(" ")[1]
                        dest_ip = self.hosts[dest_host]
                        for src_name, fd in self.iface2fd.items():
                            src_ip = self.iface[src_name].ip
                            src_mac = self.iface[src_name].mac
                            if dest_host in self.arp.table:    
                                dest_mac = self.arp_table[dest_host]["mac"]
                                print("\n################\n", msg_args)
                                data_frame = { "type": "dataframe", 
                                            "data": self.encapsualte(msg_args[-1], src_ip, src_mac, dest_ip, dest_mac)}
                                serialised_data = pickle.dumps(data_frame)
                                fd.send(serialised_data)
                            else:
                                self.pq.table[src_ip].append(msg_args[-1])
                                print("[INFO]", self.pq.table)
                                arp_frame = {
                                    "type": "arp_request",
                                    "src_ip": src_ip,
                                    "src_mac": src_mac,
                                    "dest_ip": dest_ip,
                                    "dest_mac": "FF:FF:FF:FF" if dest_ip!= src_ip else src_mac,
                                }
                                serialised_data = pickle.dumps(arp_frame)
                                for iface, fd in self.iface2fd.items():
                                    if fd != r:
                                        fd.send(serialised_data)
                    
    def encapsualte(self, msg, src_ip, src_mac, dest_ip, dest_mac):
        data_frame = DataFrame()
        data_frame.msg = msg[0].replace("\n","").strip() if msg else ""
        data_frame.dll_src_ip = src_ip
        data_frame.dll_src_mac = src_mac
        data_frame.dll_dest_ip = dest_ip
        data_frame.dll_dest_mac = dest_mac
        return data_frame
                    
    def read_file(self, filename):
        metadata = {}
        with open(filename) as file:
            lines = file.readlines()
            for line in lines:
                parsed_line = [ details.replace("\n", "").replace("\t","") for details in line.split(" ") if details!= ""]
                try:
                    if "iface" in filename and parsed_line!=['']:
                        if len(parsed_line)==4:
                            parsed_line.insert(3, '')
                        iface = Interface(parsed_line)
                        iface.print_details()
                        metadata[parsed_line[0]] = iface
                    elif parsed_line!=['']:
                        rtable = RouteTable(parsed_line)
                        rtable.print_details()
                        metadata[parsed_line[-1]] = rtable
                except Exception as e:
                        print("[ERROR]", parsed_line, e)
        return metadata
                            
def load_args():
    args = sys.argv
    if len(args) != 5:
        print("[ERROR] Invalid usage")
        exit()
    return args
    
def main():
    args = load_args()
    station = Station(args)
    station.initialize()
    
if __name__ == "__main__":
    main()