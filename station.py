import os
import sys
import socket
import select
import pickle
from collections import defaultdict
from utils.utils import Interface, RouteTable, DataFrame, ARP, Hosts, PQ, IPpacket

class Station:
    def __init__(self, params):
        self.arp = ARP()
        self.pq = PQ()
        self.iface2fd = {}
        self.fd2iface = {}
        self.ip2fd = {}
        self.isroute = True if "route" in params[1] else False
        self.iface = self.read_file(params[2])
        self.rtable = self.read_file(params[3])
        self.name = list(self.iface.keys())
        self.hosts = Hosts(params[4]).get_hosts()
     
    def get_landetails(self, lanname):
        with open("./symlinks/.{}.addr".format(lanname)) as file:
                ip = file.read()
        with open("./symlinks/.{}.port".format(lanname)) as file:
            port = file.read()         
        return ip, port
    
    def get_key(self, val, data):
        for key, value in data.items():
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
            # addr = None
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
                print("[ERROR] Cannot connect. Bridge rejected")
                sys.exit(0)

            # Get active port and IP address
            addr_info = sockfd.getsockname()
            ipstr = addr_info[0]
            port = addr_info[1]
            print("[DEBUG] Bridge accepted iface {} on '{}' at '{}' thru '{}'".format(iface_name, ipstr, bridge_ip, port))
            client_set.add(sockfd)

        while True:
            temp_set, _, _ = select.select(client_set, [], [])
            for r in temp_set:
                # print("*************",r.fileno())
                if r in client_set and r!= sys.stdin:
                    response = r.recv(4096)
                        
                    if not response:
                        print("Bridge disconnected.")
                        sys.exit(0)
                        
                    cur_iface = self.fd2iface[r]
                    data = pickle.loads(response)

                    if data["type"] == "arp_request":
                        # print("arp_request=> ",self.hosts[cur_iface],data)
                        if data["dest_ip"] == self.hosts[cur_iface]:
                            print("[DEBUG] It's My IP sending back ARP response\n")
                            data["dest_mac"] = self.iface[cur_iface].mac
                            arp_reply = self.arp.reply(data)
                            r.send(arp_reply)
                            
                    elif data["type"] == "arp_reply":
                        src_ip, src_mac, dest_ip, dest_mac = data["dest_ip"], data["dest_mac"], data["src_ip"], data["src_mac"]
                        print("[DEBUG] Received arp response from ", dest_ip)
                        self.arp.table[dest_ip] = dest_mac
                        if dest_ip in self.pq.table:
                            packets = self.pq.table[dest_ip]
                            for packet in packets:
                                data_frame = DataFrame(packet, src_mac, dest_mac)
                                encrypted_df = pickle.dumps(data_frame)
                                serialised_frame = pickle.dumps({ "type": "dataframe", "data": encrypted_df})
                                self.ip2fd[src_ip].send(serialised_frame)
                                self.pq.table[dest_ip].pop(0)
                        else:
                            print("[DEBUG] Got ARP response but pending queue is empty. Nothing to forward.")
                                
                    elif data["type"] == "dataframe":
                        data_frame = pickle.loads(data["data"])
                        if data_frame.dest_mac == self.iface[cur_iface].mac:
                            packet = pickle.loads(data_frame.packet)
                            packet.show()
                            print("{} >> {}".format(cur_iface, packet.msg))
                            
                elif r == sys.stdin:
                    msg = sys.stdin.readline()
                    if not msg:
                        sys.exit(0)
                    msg_args = msg.split(" ", 1)
                    if msg_args[0] == "send":
                        msg_args = msg.split(" ", 2)                       
                        dest_host = msg.split(" ")[1]
                        dest_ip = self.hosts[dest_host]
                        for src_name, fd in self.iface2fd.items():
                            src_ip = self.iface[src_name].ip
                            src_mac = self.iface[src_name].mac
                            ip_packet = IPpacket(msg_args[-1].replace("\n", ""), src_ip, dest_ip)
                            encapsulated_packet = pickle.dumps(ip_packet)
                            if dest_ip in self.arp.table:
                                print("[DEBUG] Entry in ARP cache")
                                dest_mac = self.arp.get(dest_ip)
                                data_frame = DataFrame(encapsulated_packet, src_mac, dest_mac)
                                encrypted_df = pickle.dumps(data_frame)
                                serialised_frame = pickle.dumps({ "type": "dataframe", "data": encrypted_df})
                                fd.send(serialised_frame)
                            else:
                                print("[DEBUG] Entry not in ARP cache. Initialising ARP request.")
                                self.pq.table[dest_ip].append(encapsulated_packet)                      # The arp request is an encrypted dict   
                                arp_request = self.arp.request(src_ip, dest_ip, src_mac)
                                for iface, fd in self.iface2fd.items():
                                    if fd != r:
                                        print("[DEBUG] Sending arp request through ",self.fd2iface[fd])
                                        fd.send(arp_request)
                                        
                    elif msg_args[0] == "show":
                        if msg_args[1] == "hosts":
                            self.hosts.show()
                        elif msg_args[1] == "arp":
                            self.arp.show()
                        elif msg_args[1] == "pq":
                            self.pq.show()
                        else:
                            print("[ERROR] INVALID REQUEST TO STATION")
                            print("AVAILABLE COMMANDS AT STATION")
                            ## print all the list of functions - [potato]
                
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
                        iface.show()
                        metadata[parsed_line[0]] = iface
                    elif parsed_line!=['']:
                        rtable = RouteTable(parsed_line)
                        rtable.show()
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