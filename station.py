import os
import sys
import socket
import select
from collections import defaultdict
from utils.interfaces import Interface
from utils.routetables import RouteTable

class Station:
    def __init__(self, params):
        self.ifaces, self.rtables = init_files()
        self.isroute = True if "route" in params[1] else False
        self.iface = self.ifaces[params[2]]
        self.rtable = self.rtables[params[3]]
        self.name = params[4]
        
    def print_details(self):
        print("""[DEBUG] Station details:
            name \t- {}
            iface_path \t- {}
            rtable_path \t\t- {}
            router \t- {}
            """.format(self.name, self.iface_path, self.rtable_path, self.type))
              
    def initialize(self):
        cur_iface = self.iface[0]
        with open("./symlinks/.{}.addr".format(self.iface[0].lanname)) as file:
            bridge_ip = file.read()
        with open("./symlinks/.{}.port".format(self.iface[0].lanname)) as file:
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
                    print(">> {}".format(data.decode()))
                if r == sys.stdin:
                    # Write client input to the server
                    data = sys.stdin.readline()
                    if not data:
                        sys.exit(0)
                    sockfd.send(data.encode())
                    
def init_files():
    dirs = ["./ifaces/", "./rtables/"]
    ifaces, rtables = defaultdict(list), defaultdict(list)
    for dir in dirs:
        for filename in os.listdir(dir):
            with open(dir + filename) as file:
                lines = file.readlines()
                for line in lines:
                    parsed_line = [ details.replace("\n", "").replace("\t","") for details in line.split(" ") if details!= ""]
                    try:
                        if "iface" in dir and parsed_line!=['']:
                            if len(parsed_line)==4:
                                parsed_line.insert(3, '')
                            iface = Interface(parsed_line)
                            # iface.print_interface()
                            ifaces[filename].append(iface)
                        elif parsed_line!=['']:
                            rtable = RouteTable(parsed_line)
                            # rtable.print_routetable()
                            rtables[filename].append(rtable)
                    except:
                            print("[ERROR]", parsed_line)
    return ifaces, rtables
                            
def load_args():
    args = sys.argv
    if len(args) != 5:
        print("[ERROR] Invalid usage")
        exit()
    return args
    
def main():
    # init_files()
    args = load_args()
    station = Station(args)
    station.initialize()
    # station.print_details()
    
if __name__ == "__main__":
    main()