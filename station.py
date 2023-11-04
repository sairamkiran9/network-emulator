import sys
import socket
import select

class Station:
    def __init__(self, params):
        self.isroute = True if "route" in params[1] else False
        self.iface_path = params[2]
        self.rtable_path = params[3]
        self.name = params[4]
        
    def print_details(self):
        print("""[DEBUG] Station details:
            name \t- {}
            iface_path \t- {}
            rtable_path \t\t- {}
            router \t- {}
            """.format(self.name, self.iface_path, self.rtable_path, self.type))
              
    def initialize(self):
        server_name = "localhost"
        port = 35916

        hints = socket.getaddrinfo(server_name, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
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
        print("Client: connected to server on '{}' at '{}' thru '{}'".format(ipstr, server_name, port))

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
                
def load_args():
    args = sys.argv
    print(len(args))
    if len(args) != 5:
        print("[ERROR] Invalid usage")
        exit()
    return args
    
def main():
    args = load_args()
    station = Station(args)
    station.initialize()
    station.print_details()
    
if __name__ == "__main__":
    main()