import os
import sys
import socket
import select
from collections import defaultdict
# from utils.interfaces import Interface
# from utils.routetables import RouteTable
from utils.utils import Interface, RouteTable, DataFrame, ARP

class Station:
    def __init__(self, params):
        self.isroute = True if "route" in params[1] else False
        self.iface = self.read_file(params[2])
        self.rtable = self.read_file(params[3])
        self.name = list(self.iface.keys())
        
    def print_details(self):
        print("""[DEBUG] Station details:
            name \t- {}
            iface_path \t- {}
            rtable_path \t\t- {}
            router \t- {}
            """.format(self.name, self.iface_path, self.rtable_path, self.type))
              
    def initialize(self):
        cur_iface = self.iface[self.name[0]]
        print(cur_iface[0].lanname)
        with open("./symlinks/.{}.addr".format(cur_iface[0].lanname)) as file:
            bridge_ip = file.read()
        with open("./symlinks/.{}.port".format(cur_iface[0].lanname)) as file:
            port = file.read()
        hints = socket.getaddrinfo(bridge_ip, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        addr = None
        for addr in hints:
            try:
                sockfd = socket.socket(addr[0], addr[1], addr[2])
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
                    data = r.recv(100)
                    if not data:
                        print("Server disconnected.")
                        sys.exit(0)
                    print("{} >> {}".format(self.name, data.decode()))
                if r == sys.stdin:
                    # Write client input to the server
                    msg = sys.stdin.readline()
                    if not msg:
                        sys.exit(0)
                    data_frame = self.encapsualte(msg)
                    
                    sockfd.send(data.encode())
                    
    def encapsualte(self, data):
        data_frame = DataFrame()
                    
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