import os
import sys
import socket
import select
import pickle
from utils.utils import Interface, RouteTable, DataFrame, ARP
          
class Bridge:
    def __init__(self, params):
        self.name = params[1]
        self.capacity = int(params[2])
        self.host_ip = ""
        self.host_port = -1
        
    def print_details(self):
        print("""[DEBUG] Bridge details:
            name \t- {}
            capacity \t- {}
            ip \t\t- {}
            port \t- {}
            """.format(self.name, self.capacity, self.host_ip, self.host_port))
                    
    def inititalize(self):
        print("[INFO] Initializing bridge")
        
        sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sockfd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sockfd.bind(('', 0))
        sockfd.listen(5)

        self.host_ip = socket.gethostname()
        self.host_port = sockfd.getsockname()[1]
        print("[INFO] Bridge intitalized on {} on port {}".format(self.host_ip, self.host_port))
        print("[INFO] Creating symlink for {}".format(self.name))
        self.create_symlink()

        main_fdset = [sockfd]
        sock_vector = []

        while True:
            new_fdset, _, _ = select.select(main_fdset, [], [])
            for r in new_fdset:
                if r == sockfd:
                    new_conn_sockfd, new_conn_addr = sockfd.accept()
                    addr_info = new_conn_sockfd.getpeername()
                    print("[INFO] Bridge: connect from '{}' {} {}:{}".format(self.host_ip,new_conn_addr, addr_info[0] , addr_info[1]))
                    sock_vector.append(new_conn_sockfd)
                    main_fdset.append(new_conn_sockfd)
                else:
                    data = r.recv(4096)
                    if not data:
                        addr_info = r.getpeername()
                        print("[INFO] Bridge: disconnect from {}:{}".format(addr_info[0],addr_info[1]))
                        r.close()
                        main_fdset.remove(r)
                        sock_vector.remove(r)
                    else:
                        # print("{}:{}: {}".format(addr_info[0], addr_info[1], data))
                        self.broadcast_msg(data, r, sock_vector)
                    
    def create_symlink(self):
        symlink_path_to_host = "./symlinks/.{}.addr".format(self.name)
        symlink_path_to_port = "./symlinks/.{}.port".format(self.name)
        
        with open(symlink_path_to_host, "w") as file:
            file.write(self.host_ip)
            
        with open(symlink_path_to_port, "w") as file:
            file.write(str(self.host_port))

        print("[INFO] Created symlink for {}".format(self.name))


    def broadcast_msg(self, data_frame, cur_fd, sock_vector):
        deseriablised_msg = pickle.loads(data_frame)
        deseriablised_msg.print_dataframe()
        serialised_msg = pickle.dumps(deseriablised_msg)
        # print(sock_vector)
        for fd in sock_vector:
            if cur_fd != fd:
                fd.send(serialised_msg)
                

def load_args():
    args = sys.argv
    if len(args) != 3:
        print("[ERROR] Invalid usage")
        exit()
    return args
    
def main():
    args = load_args()
    bridge = Bridge(args)
    bridge.inititalize()
    bridge.print_details()
    
if __name__ == "__main__":
    main()