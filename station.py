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
        
    def print_details(self):
        print("""[DEBUG] Station details:
            name \t- {}
            iface_path \t- {}
            rtable_path \t\t- {}
            router \t- {}
            """.format(self.name, self.isroute, self.rtable, self.iface))
              
    def initialize(self):
        cur_iface = self.iface[self.name[0]]
        with open("./symlinks/.{}.addr".format(cur_iface[0].lanname)) as file:
            bridge_ip = file.read()
        with open("./symlinks/.{}.port".format(cur_iface[0].lanname)) as file:
            port = file.read()
        hints = socket.getaddrinfo(bridge_ip, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        addr = None
        for addr in hints:
            try:
                sockfd = socket.socket(addr[0], addr[1], addr[2])
                station_ip = self.hosts[self.name[0]]
                print("station - ", self.name[0], station_ip)
                sockfd.connect(addr[4])
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
        print("Client: connected to server on '{}' at '{}' thru '{}'".format(ipstr, bridge_ip, port))

        client_set = set()
        client_set.add(sys.stdin)
        client_set.add(sockfd)

        if sockfd.fileno() > sys.stdin.fileno():
            max_fd = sockfd.fileno() + 1
        else:
            max_fd = sys.stdin.fileno() + 1

        while True:
            temp_set, _, _ = select.select(client_set, [], [])
            for r in temp_set:
                if r == sockfd:
                    # Read server response
                    data_frame = r.recv(4096)
                    if not data_frame:
                        print("Server disconnected.")
                        sys.exit(0)
                    data = pickle.loads(data_frame)
                    if data["type"] == "arp_request":
                        for station in self.name:
                            if data["dest_ip"] == self.hosts[station]:
                                data["dest_mac"] = self.iface[station][0].mac
                                data["type"] = "arp_reply"
                                serialised_arp = pickle.dumps(data) 
                                r.send(serialised_arp)
                    elif data["type"] == "arp_reply":
                        dest_ip = data["dest_ip"]
                        self.arp.cache[dest_ip] = data["dest_mac"]
                        self.arp.table[dest_ip] = data["dest_mac"]
                        if dest_ip in self.pq.table:
                            data_frame = { "type": "dataframe", "data": self.encapsualte(self.pq.table[data["dest_ip"]], data["src_ip"], data["src_mac"], data["dest_ip"], data["dest_mac"])}
                            self.pq.table[data["dest_ip"]].pop(0)
                            serialised_data = pickle.dumps(data_frame)
                            sockfd.send(serialised_data)
                    elif data["data"].dll_dest_mac == self.iface[self.name[0]][0].mac:
                        data["data"].print_dataframe()
                        print("{} >> {}".format(self.name[0], data["data"].msg))
                if r == sys.stdin:
                    # Write client input to the server
                    msg = sys.stdin.readline()
                    if not msg:
                        sys.exit(0)
                    msg_args = msg.split(" ", 3)
                    if msg_args[0] == "send":
                        src_name = self.name[0]  
                        dest_host = msg.split(" ")[1]
                        dest_ip = self.hosts[dest_host]
                        src_ip = self.iface[src_name][0].ip
                        src_mac = self.iface[src_name][0].mac
                        if dest_host in self.arp.table or dest_host in self.arp.cache :    
                            dest_mac = self.arp_table[dest_host]["mac"]
                            data_frame = { "type": "dataframe", 
                                          "data": self.encapsualte(msg_args[-1], src_ip, src_mac, dest_ip, dest_mac)}
                            serialised_data = pickle.dumps(data_frame)
                            sockfd.send(serialised_data)
                        else:
                            self.pq.table[dest_ip].append(msg_args[-1])
                            print("[INFO]", self.pq.table)
                            arp_frame = {
                                "type": "arp_request",
                                "src_ip": src_ip,
                                "src_mac": src_mac,
                                "dest_ip": dest_ip,
                                "dest_mac": "FF:FF:FF:FF",
                            }
                            serialised_data = pickle.dumps(arp_frame)
                            sockfd.send(serialised_data)
                    
    def encapsualte(self, msg, src_ip, src_mac, dest_ip, dest_mac):
        data_frame = DataFrame()
        data_frame.msg = msg[0].replace("\n","").strip()
        data_frame.dll_src_ip = src_ip
        data_frame.dll_src_mac = src_mac
        data_frame.dll_dest_ip = dest_ip
        data_frame.dll_dest_mac = dest_mac
        return data_frame
                    
    def read_file(self, filename):
        metadata = defaultdict(list)
        with open(filename) as file:
            lines = file.readlines()
            for line in lines:
                parsed_line = [ details.replace("\n", "").replace("\t","") for details in line.split(" ") if details!= ""]
                try:
                    if "iface" in filename and parsed_line!=['']:
                        if len(parsed_line)==4:
                            parsed_line.insert(3, '')
                        iface = Interface(parsed_line)
                        iface.print_interface()
                        metadata[parsed_line[0]].append(iface)
                    elif parsed_line!=['']:
                        rtable = RouteTable(parsed_line)
                        rtable.print_routetable()
                        metadata[parsed_line[-1]].append(rtable)
                except:
                        print("[ERROR]", parsed_line)
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