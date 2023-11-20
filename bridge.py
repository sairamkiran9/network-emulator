"""
bridge.py: The main functionality of station and router
Authors:
- Sri Sai Ram Kiran Muppana
- [potato]
"""

import sys
import time
import socket
import select
import pickle
from utils.utils import ARP, SL


class Bridge:
    def __init__(self, params):
        self.name = params[1]
        self.capacity = int(params[2])
        self.host_ip = ""
        self.host_port = -1
        self.sl = SL()
        self.arp = ARP()
        self.sock_vector = []

    def check_connection(self, sockfd, nconn):
        time.sleep(2)
        accept_signal = sockfd.recv(4096)
        if accept_signal and self.capacity > nconn:
            print(
                "[INFO] I accepted connection request from station at fd .", sockfd.fileno())
            sockfd.send("Accepted connection".encode())
            return True
        elif self.capacity <= nconn:
            print(
                "[ERROR] New connectin rejected because i'm full and all my ports are occupied!")
            sockfd.close()
            return False

    def inititalize(self):
        print("[INFO] Initializing bridge")
        sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sockfd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sockfd.bind(('', 0))
        sockfd.listen(self.capacity)
        self.host_ip = socket.gethostname()
        self.host_port = sockfd.getsockname()[1]
        print("[INFO] Bridge intitalized on {} on port {}".format(
            self.host_ip, self.host_port))
        print("[INFO] Creating symlink for {}".format(self.name))
        self.create_symlink()

        main_fdset = set([sys.stdin, sockfd])
        # self.sock_vector = []
        while 1:
            new_fdset, _, _ = select.select(main_fdset, [], [])
            for r in new_fdset:
                nconnections = len(self.sock_vector)
                if r == sys.stdin:
                    msg = sys.stdin.readline()
                    if not msg:
                        sys.exit(0)
                    msg_args = msg.split(" ", 1)
                    print(msg_args)
                    if msg_args[0] == "show":
                        if msg_args[1].replace("\n", "") == "sl":
                            self.sl.show()
                    else:
                        print("[DEBUG] Command not valid")
                elif r == sockfd:
                    try:
                        new_conn_sockfd, new_conn_addr = sockfd.accept()
                        if not self.check_connection(new_conn_sockfd, nconnections):
                            break
                        addr_info = new_conn_sockfd.getpeername()
                        print("[INFO] Bridge: connect from '{}' {}:{}".format(
                            self.host_ip, addr_info[0], addr_info[1]))
                        self.sock_vector.append(new_conn_sockfd)
                        main_fdset.add(new_conn_sockfd)
                    except socket.error as e:
                        print(f"Error accepting connection: {e}")
                        break
                elif nconnections > 0:
                    data = r.recv(4096)
                    if not data:
                        addr_info = r.getpeername()
                        print("[INFO] Bridge: disconnect from {}:{}".format(
                            addr_info[0], addr_info[1]))
                        r.close()
                        main_fdset.remove(r)
                        self.sock_vector.remove(r)
                    else:
                        self.handle_frame(data, r)
        return True

    def create_symlink(self):
        symlink_path_to_host = "./symlinks/.{}.addr".format(self.name)
        symlink_path_to_port = "./symlinks/.{}.port".format(self.name)

        with open(symlink_path_to_host, "w") as file:
            file.write(self.host_ip)

        with open(symlink_path_to_port, "w") as file:
            file.write(str(self.host_port))

        print("[INFO] Created symlink for {}".format(self.name))

    def handle_frame(self, data_frame, cur_fd):
        frame = pickle.loads(data_frame)
        cur_port = self.sock_vector.index(cur_fd)
        if frame["type"] == "arp_request":
            dest_mac = frame["dest_mac"]
            src_mac = frame["src_mac"]
            if dest_mac in self.sl.table:
                print("[INFO] Entry in SL table")
                arp_reply = self.arp.reply(frame)
                forward_fd = self.sl.get(dest_mac)
                forward_fd.send(arp_reply)

            elif frame["dest_ip"] == frame["src_ip"]:
                print("[DEBUG] Sending arp reply to same port.")
                self.sl.add_entry(src_mac, cur_fd, cur_port)
                frame["dest_mac"] = frame["src_mac"]
                arp_reply = self.arp.reply(frame)
                cur_fd.send(arp_reply)

            else:
                cur_port = self.sock_vector.index(cur_fd)
                print("[INFO] Sending ARP Request to neighbours from port", cur_port)
                self.sl.add_entry(src_mac, cur_fd, cur_port)
                print(frame["src_ip"],
                      frame["dest_ip"], "**\n")
                for fd in self.sock_vector:
                    if cur_fd != fd:
                        fd.send(data_frame)

        elif frame["type"] == "arp_reply":
            dest_mac = frame["dest_mac"]
            src_mac = frame["src_mac"]
            src_port = self.sock_vector.index(cur_fd)
            self.sl.add_entry(src_mac, cur_fd, src_port)
            forward_fd = self.sl.get(dest_mac)
            cur_port = self.sock_vector.index(forward_fd)
            print("[INFO] Got ARP Response, forwarding it to port ", cur_port)
            forward_fd.send(data_frame)

        elif frame["type"] == "dataframe":
            df = pickle.loads(frame["data"])
            if df.dest_mac in self.sl.table:
                station_fd = self.sl.get(df.dest_mac)
                station_fd.send(data_frame)
            else:
                print("[INFO] Entry not in SL table. Broadcasting the message.")
                for fd in self.sock_vector:
                    if fd != cur_fd:
                        fd.send(data_frame)


def load_args():
    args = sys.argv
    if len(args) != 3:
        print("[ERROR] Invalid usage")
        exit()
    return args


def main():
    args = load_args()
    bridge = Bridge(args)
    isInitialised = bridge.inititalize()
    if isInitialised:
        bridge.show()


if __name__ == "__main__":
    main()
