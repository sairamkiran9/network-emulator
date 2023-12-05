"""
bridge.py: The main functionality of station and router
Authors:
- Sri Sai Ram Kiran Muppana
- Sahithi Vungarala
"""

import os
import sys
import signal
import socket
import select
import pickle
from utils.sl import SL
from utils.arp import ARP
from utils.utils import handle_interupt


class Bridge:
    """
    Bridge class that represents complete bridge functionality.
    """

    def __init__(self, params):
        """default constructor

        Args:
            params (list): contains input commands of user
        """
        self.name = params[1]
        self.capacity = int(params[2])
        self.host_ip = ""
        self.host_port = -1
        self.sl = SL()          # SL intialization
        self.arp = ARP()
        self.sock_vector = []   # vector to store socket file descriptors

    def check_connection(self, sockfd, nconn):
        """_summary_

        Args:
            sockfd (socket object): file descriptor object of socket
            nconn (integer): current number of connections

        Returns:
            bool: Returns the decision to accept or reject the connection
        """
        if self.capacity > nconn:
            print(
                "[INFO] I accepted connection request from station at fd .", sockfd.fileno())
            # send accept message to the connected station
            sockfd.send("accept".encode())
            return True
        elif self.capacity <= nconn:
            print(
                "[ERROR] New connectin rejected because i'm full and all my ports are occupied!")
            # send reject message to the connected station
            sockfd.send("reject".encode())
            sockfd.close()
            return False

    def inititalize(self):
        """This method creates a socket and starts listening to 
        accept new connections followed by non-blocking (using selector)
        monitoring of user inputs from terminal and data received from
        stations

        Returns:
            bool: Returns true if bridge is intialised
        """
        print("[INFO] Initializing bridge")
        sockfd = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)   # socket init
        sockfd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sockfd.bind(('', 0))
        sockfd.listen(self.capacity)    # socket listening
        self.host_ip = socket.gethostname()
        self.host_port = sockfd.getsockname()[1]
        print("[INFO] Bridge intitalized on {} on port {}".format(
            self.host_ip, self.host_port))
        print("[INFO] Creating symlink for {}".format(self.name))
        self.create_symlink()    # storing ip and port details (symlinks)

        main_fdset = set([sys.stdin, sockfd])
        while 1:
            new_fdset, _, _ = select.select(main_fdset, [], [])  # selector()
            print("Bridge>")
            for r in new_fdset:
                nconnections = len(self.sock_vector)
                if r == sys.stdin:  # user input
                    msg = sys.stdin.readline()
                    if not msg:
                        self.quit()
                    msg_args = msg.split(" ", 1)
                    if msg_args[0] == "show":
                        if msg_args[1].replace("\n", "") == "sl":
                            self.sl.show()
                        else:
                            print("[DEBUG] Command not valid")
                    elif "quit" in msg_args[0]:
                        print("[INFO] Closing bridge.")
                        self.quit()
                    else:
                        print("[DEBUG] Command not valid")
                elif r == sockfd:  # connected stations
                    try:
                        new_conn_sockfd, new_conn_addr = sockfd.accept()
                        # check connection to accept or reject the bridge
                        if self.check_connection(new_conn_sockfd, nconnections):
                            addr_info = new_conn_sockfd.getpeername()
                            print("[INFO] Bridge: connect from '{}' {}:{}".format(
                                self.host_ip, addr_info[0], addr_info[1]))
                            self.sock_vector.append(new_conn_sockfd)
                            main_fdset.add(new_conn_sockfd)
                            nconnections += 1
                    except socket.error as e:
                        print("Error accepting connection:".format(e))
                        break
                elif nconnections > 0:
                    data = r.recv(4096)  # recv data from connected stations
                    if not data:
                        # delete details from the dict and fdset when the staion is disconnected
                        addr_info = r.getpeername()
                        print("[INFO] Bridge: disconnect from {}:{}".format(
                            addr_info[0], addr_info[1]))
                        r.close()
                        main_fdset.remove(r)
                        self.sock_vector.remove(r)
                        self.sl.remove_entry(r)
                    else:
                        self.handle_frame(data, r)
        return True

    def quit(self):
        """clean files and exit the program
        """
        os.remove("./symlinks/.{}.addr".format(self.name))
        os.remove("./symlinks/.{}.port".format(self.name))
        sys.exit(0)

    def create_symlink(self):
        """create dir if not exits and strore files with ip and port info
        """
        symlink_path_to_host = "./symlinks/.{}.addr".format(self.name)
        symlink_path_to_port = "./symlinks/.{}.port".format(self.name)
        if (not os.path.isdir("./symlinks/")):
            os.mkdir("./symlinks/")
        with open(symlink_path_to_host, "w") as file:
            file.write(self.host_ip)

        with open(symlink_path_to_port, "w") as file:
            file.write(str(self.host_port))

        print("[INFO] Created symlink for {}".format(self.name))

    def handle_frame(self, data_frame, cur_fd):
        """Handling of incoming frame from the connected stations
        Decision is made based on the SL cache i.e. to broadcast or to 
        forward to a designated port.

        Args:
            data_frame (Dataframe object): It may contain arp or dataframe object
            cur_fd (socket object): socket details from where the response is received
        """
        frame = pickle.loads(data_frame)
        cur_port = self.sock_vector.index(cur_fd)
        if frame["type"] == "arp_request":
            dest_mac = frame["dest_mac"]
            src_mac = frame["src_mac"]
            if dest_mac in self.sl.table:   # check entry in SL
                print("[INFO] Entry in SL table")
                self.sl.table[dest_mac]["timer"] = 60  # updating timer
                forward_fd = self.sl.get(dest_mac)
                forward_fd.send(data_frame)

            else:
                cur_port = self.sock_vector.index(cur_fd)
                print("[INFO] Sending ARP Request to neighbours from port", cur_port)
                # Adding entry to SL cache
                self.sl.add_entry(src_mac, cur_fd, cur_port)
                for fd in self.sock_vector:  # Broadcasting the frame
                    if cur_fd != fd:
                        fd.send(data_frame)

        elif frame["type"] == "arp_reply":
            dest_mac = frame["dest_mac"]
            src_mac = frame["src_mac"]
            src_port = self.sock_vector.index(cur_fd)
            # Adding entry to SL cache
            self.sl.add_entry(src_mac, cur_fd, src_port)
            forward_fd = self.sl.get(dest_mac)
            cur_port = self.sock_vector.index(forward_fd)
            print("[INFO] Got ARP Response, forwarding it to port ", cur_port)
            forward_fd.send(data_frame)

        elif frame["type"] == "dataframe":
            df = pickle.loads(frame["data"])
            if df.dest_mac in self.sl.table:  # check entry in SL
                self.sl.table[df.dest_mac]["timer"] = 60  # updating timer
                station_fd = self.sl.get(df.dest_mac)
                if station_fd in self.sock_vector:
                    station_fd.send(data_frame)
                else:
                    print("[DEBUG] I think station with this {} disconnected")
            else:
                print("[INFO] Entry not in SL table. Broadcasting the message.")
                for fd in self.sock_vector:
                    if fd != cur_fd:  # Broadcasting the frame
                        fd.send(data_frame)


def load_args():
    """validates user input 

    Returns:
        list: parsed user input commands
    """
    args = sys.argv
    if len(args) != 3:
        print("[ERROR] Invalid usage")
        exit()
    return args


def main():
    """main method to load user args and start bridge
    """
    args = load_args()
    signal.signal(signal.SIGINT, handle_interupt)
    bridge = Bridge(args)
    isInitialised = bridge.inititalize()
    if isInitialised:
        bridge.show()


if __name__ == "__main__":
    """script init
    """
    main()
