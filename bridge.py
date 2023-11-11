import os
import sys
import socket
import select
import pickle
from utils.utils import Interface, RouteTable, DataFrame, ARP, SL


class Bridge:
    def __init__(self, params):
        self.name = params[1]
        self.capacity = int(params[2])
        self.host_ip = ""
        self.host_port = -1
        self.sl = SL()
        self.arp = ARP()

    def inititalize(self):
        print("[INFO] Initializing bridge")
        sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sockfd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sockfd.bind(('', 0))
        sockfd.listen(5)
        self.host_ip = socket.gethostname()
        self.host_port = sockfd.getsockname()[1]
        print("[INFO] Bridge intitalized on {} on port {}".format(
            self.host_ip, self.host_port))
        print("[INFO] Creating symlink for {}".format(self.name))
        self.create_symlink()

        main_fdset = [sockfd]
        sock_vector = []

        while len(sock_vector) <= self.capacity:
            new_fdset, _, _ = select.select(main_fdset, [], [])
            for r in new_fdset:
                if r == sockfd:
                    new_conn_sockfd, new_conn_addr = sockfd.accept()
                    addr_info = new_conn_sockfd.getpeername()
                    print("[INFO] Bridge: connect from '{}' {} {}:{}".format(
                        self.host_ip, new_conn_addr, addr_info[0], addr_info[1]))
                    sock_vector.append(new_conn_sockfd)
                    main_fdset.append(new_conn_sockfd)
                else:
                    data = r.recv(4096)
                    if not data:
                        addr_info = r.getpeername()
                        print("[INFO] Bridge: disconnect from {}:{}".format(
                            addr_info[0], addr_info[1]))
                        r.close()
                        main_fdset.remove(r)
                        sock_vector.remove(r)
                    else:
                        self.broadcast_msg(data, r, sock_vector)

        if len(sock_vector) > self.capacity:
            print("[ERROR] Bridge is full. All ports are occupied!")

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
        if deseriablised_msg["type"] == "arp_request":
            dest_mac = deseriablised_msg["dest_mac"]
            src_mac = deseriablised_msg["src_mac"]
            if dest_mac in self.sl.table:
                print("[INFO] Entry in SL table")
                arp_reply = self.arp.reply(deseriablised_msg)
                cur_fd.send(arp_reply)

            elif deseriablised_msg["dest_ip"] == deseriablised_msg["src_ip"]:
                print("[DEBUG] Sending arp request to myself.")
                self.sl.table[src_mac] = cur_fd
                cur_fd.send(data_frame)

            else:
                cur_port = sock_vector.index(cur_fd)
                print("[INFO] Sending ARP Request to neighbours from port", cur_port)
                self.sl.table[src_mac] = cur_fd
                print(deseriablised_msg["src_ip"], deseriablised_msg["dest_ip"], "**\n")
                for fd in sock_vector:
                    if cur_fd != fd:
                        fd.send(data_frame)

        elif deseriablised_msg["type"] == "arp_reply":
            dest_mac = deseriablised_msg["dest_mac"]
            src_mac = deseriablised_msg["src_mac"]
            self.sl.table[src_mac] = cur_fd
            forward_fd = self.sl.table[dest_mac]
            cur_port = sock_vector.index(forward_fd)
            print("[INFO] Got ARP Response, forwarding it to port ", cur_port)
            forward_fd.send(data_frame)

        elif deseriablised_msg["type"] == "dataframe":
            print("[DEBUG] Self-Learning Table \n", self.sl.table.keys())
            df = pickle.loads(deseriablised_msg["data"])
            if df.dest_mac in self.sl.table:
                station_fd = self.sl.table[df.dest_mac]
                station_fd.send(data_frame)


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
    bridge.show()


if __name__ == "__main__":
    main()
