"""
station.py: The main functionality of station and router
Authors:
- Sri Sai Ram Kiran Muppana
- Sahithi Vungarala
"""

import os
import signal
import sys
import time
import socket
import select
import pickle
from utils.pq import PQ
from utils.arp import ARP
from utils.hosts import Hosts
from utils.packet import IPpacket
from utils.route import RouteTable
from utils.utils import handle_interupt
from utils.utils import Interface, DataFrame


class Station:
    """station implemenation
    """

    def __init__(self, params):
        """Default constructor, intializes arp, pending queue
        and loads all ifaces, tables and hosts file.

        Args:
            params (list): input params for iface, rtable and hosts paths
        """
        self.arp = ARP()    # arp init
        self.pq = PQ()      # pq init
        self.iface2fd = {}
        self.fd2iface = {}
        self.ip2fd = {}
        self.isroute = True if "route" in params[1] else False
        self.iface = self.read_file(params[2])
        self.rtable = self.read_file(params[3])
        self.name = list(self.iface.keys())
        self.hosts = Hosts(params[4])   # hosts init
        self.display()

    def display(self):
        """Display Iface tables, rtables and hosts
        """
        Interface.show_ifaces(self.iface)
        RouteTable.show_rtables(self.rtable)
        self.hosts.show()

    def get_landetails(self, lanname):
        """Reads symbolics of lanname

        Args:
            lanname (string): bridge name to fetch ip, port details

        Raises:
            Exception: _description_

        Returns:
            string, string: ip, port details
        """
        if not os.path.exists("./symlinks/.{}.addr".format(lanname)):
            print("[ERROR] Bidge details missing")
            raise Exception
        with open("./symlinks/.{}.addr".format(lanname)) as file:
            ip = file.read()
        with open("./symlinks/.{}.port".format(lanname)) as file:
            port = file.read()
        return ip, port

    def check_connection(self, sockfd, iface):
        """checks the handshake between bridge and station

        Args:
            sockfd (socket object): file descriptor
            iface (string): current interface name

        Returns:
            bool: True if station is connected
        """
        print("[DEBUG] Checking new connection to bridge...")
        accept_signal = sockfd.recv(4096)
        status = accept_signal.decode()
        if status == "accept":  # recv "accept" from bridge
            message = "[{}][INFO] Bridge accepted my connection request".format(
                iface)
            print("\n{}\n".format(message))
            return True
        else:
            print(
                "[{}][ERROR] Bridge rejected my connection request".format(iface))
            return False

    def get_nexthop(self, ip, cur_iface):
        """nexthop calculation

        Args:
            ip (string): destination ip for nexthop calculation
            cur_iface (string): current interface

        Returns:
            string: nexthop ip
        """
        print("[DEBUG] Calculating next hop")
        next_hop = ""
        for rtable in self.rtable:
            next_hop = rtable.route(ip)
            if next_hop != "" and next_hop != "0.0.0.0":
                return next_hop, rtable.iface
            if next_hop == "0.0.0.0":
                print("[DEBU] Returning dest ip since next hop is 0.0.0.0")
                return ip, rtable.iface
        if next_hop == "":
            for rtable in self.rtable:
                if rtable.dest_ip == "0.0.0.0":  # default gateway
                    print("[INFO] Default gateway router")
                    return rtable.next_hop, rtable.iface
        return ip, cur_iface

    def init_arp_request(self, encapsulated_packet, src_ip, src_mac, next_hop, fd):
        """Creates an arp request object and forwards it

        Args:
            encapsulated_packet (IPpacket object): IPpacket that goes into pending queue 
            src_ip (string): source ip
            src_mac (string): source mac
            next_hop (string): nexthop ip
            fd (socket object): fd to send
        """
        arp_request = self.arp.request(src_ip, next_hop, src_mac)
        print("[DEBUG] Sending arp request of size {} bytes through {}".format(
            len(arp_request), self.fd2iface[fd]))
        fd.send(arp_request)

    def connect_bridge(self):
        """Retry mechanism

        Returns:
            set: set of connected file descriptors
        """
        station_set = set()
        station_set.add(sys.stdin)
        ntries = 0
        status = False
        while ntries < 5:
            ntries += 1
            for iface_name in self.iface:
                if iface_name not in self.iface2fd:
                    try:
                        sockfd = None
                        status = False
                        print("[INFO] Initializing interface ", iface_name)
                        cur_iface = self.iface[iface_name]
                        bridge_ip, port = self.get_landetails(
                            cur_iface.lanname)  # read bridge ip, port
                        hints = socket.getaddrinfo(
                            bridge_ip, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
                        addr = hints[0]
                        sockfd = socket.socket(addr[0], addr[1], addr[2])
                        sockfd.setblocking(0)   # setting non blocking io mode
                        sockfd.settimeout(2)
                        sockfd.connect(addr[4])  # connecting to bridge
                        temp_set, _, _ = select.select([sockfd], [], [])
                        for sockfd in temp_set:
                            # check for intial handshake
                            status = self.check_connection(sockfd, iface_name)
                            if status:
                                station_set.add(sockfd)
                                station_ip = self.hosts.get_hosts(iface_name)
                                # save details to dictionaries
                                self.iface2fd[iface_name] = sockfd
                                self.fd2iface[sockfd] = iface_name
                                self.ip2fd[station_ip] = sockfd
                            else:
                                sockfd.close()
                        sockfd.setblocking(1)
                    except socket.error as e:
                        if sockfd:
                            sockfd.close()
                        if e.errno == socket.errno.EINPROGRESS:
                            pass
                        else:
                            print(
                                "[{}][ERROR] Station connecting to bridge failed. Number of tries = {}".format(iface_name, ntries))
                    except Exception as e:
                        print(e)
                        print("[{}][ERROR] Bridge not intialised. Number of tries = {}".format(
                            iface_name, ntries))

            if len(station_set) == len(self.iface)+1:
                break
            time.sleep(2)

        if len(station_set) != len(self.iface)+1:
            sys.exit(0)
        return station_set

    def initialize(self):
        """Monitors send and recv data from bridge and takes respective action
        """
        station_set = self.connect_bridge()
        while True:
            header = "\nStation>" if not self.isroute else "\nRouter>"
            print(header)
            temp_set, _, _ = select.select(station_set, [], [])  # selector()
            for r in temp_set:
                if r in station_set and r != sys.stdin:  # recv data
                    response = r.recv(20000)
                    if not response:
                        print("Bridge disconnected.")
                        station_set.remove(r)
                        sys.exit(0)
                    cur_iface = self.fd2iface[r]
                    data = pickle.loads(response)
                    if data["type"] == "arp_request":
                        if data["dest_ip"] == self.hosts.get_hosts(cur_iface):
                            print("[DEBUG] It's My IP sending back ARP response.")
                            data["dest_mac"] = self.iface[cur_iface].mac
                            if data["src_ip"] in self.arp.table:
                                print(
                                    "[DEBUG] Entry already in arp cache. Updating the timer")
                            self.arp.add_entry(data["src_ip"], data["src_mac"])
                            arp_reply = self.arp.reply(data)
                            r.send(arp_reply)
                        else:
                            print(
                                "[DEBUG] Received ARP request. This IP packet is not for me")

                    elif data["type"] == "arp_reply":
                        src_ip, src_mac, dest_ip, dest_mac = data["dest_ip"], data[
                            "dest_mac"], data["src_ip"], data["src_mac"]
                        print("[DEBUG] Received arp response of size {} bytes from {}".format(
                            len(data), dest_mac))
                        if dest_ip in self.arp.table:
                            print(
                                "[DEBUG] Entry already in arp cache. Updating the timer")
                        self.arp.add_entry(dest_ip, dest_mac)
                        if dest_ip in self.pq.table:
                            packets = self.pq.table[dest_ip]
                            for packet in packets:
                                print(packet.msg)
                                data_frame = DataFrame(
                                    packet, src_ip, dest_ip, src_mac, dest_mac)
                                encrypted_df = pickle.dumps(data_frame)
                                serialised_frame = pickle.dumps(
                                    {"type": "dataframe", "data": encrypted_df})
                                print("[DEBUG] Sending dataframe to", dest_mac)
                                packet.show()
                                r.send(serialised_frame)
                                # self.pq.remove_entry(dest_ip, i)
                                time.sleep(2)
                            del self.pq.table[dest_ip]
                            print("sent")
                        else:
                            print(
                                "[DEBUG] Got ARP response but pending queue is empty. Nothing to forward.")

                    elif data["type"] == "dataframe":
                        data_frame = pickle.loads(data["data"])
                        print("[INFO] Received frame of size {} bytes to {}.\nMy mac address is {}".format(
                            len(data["data"]), data_frame.dest_mac, self.iface[cur_iface].mac))
                        if data_frame.dest_mac == self.iface[cur_iface].mac:
                            ip_packet = data_frame.packet
                            ip_packet.show()
                            if ip_packet.dest_ip == self.iface[cur_iface].ip and not self.isroute:
                                print("This IP packet is received from station {}".format(
                                    data_frame.dest_mac))
                                print("{} >> {}".format(
                                    cur_iface, ip_packet.msg))
                            else:
                                print(
                                    "[DEBUG] I'm a router, forwarding the received packet.")
                                print("[DEBUG] current details",
                                      ip_packet.dest_ip, cur_iface)
                                next_hop, next_iface = self.get_nexthop(
                                    ip_packet.dest_ip, cur_iface)
                                print("[DEBUG] Next hop ip ", next_hop)
                                print("[DEBUG] Next hop interface", next_iface)
                                self.pq.table[next_hop].append(
                                    data_frame.packet)
                                print(
                                    "[DEBUG] Entry not in ARP cache. Initialising ARP request.")
                                print("Added IPpacket to queue.")
                                self.init_arp_request(
                                    data_frame.packet, self.iface[next_iface].ip, self.iface[next_iface].mac, next_hop, self.iface2fd[next_iface])

                elif r == sys.stdin:  # user input handling
                    msg = sys.stdin.readline()
                    if not msg:
                        sys.exit(0)
                    msg_args = msg.split(" ", 1)
                    if msg_args[0] == "send" and self.isroute != "route":
                        msg_args = msg.split(" ", 2)
                        dest_host = msg.split(" ")[1]
                        if dest_host not in self.hosts.hosts:
                            print("[ERROR] Unrecognised host.",
                                  dest_host.replace("\n", ""), " not in DNS")
                            break
                        # nexthop calculation
                        dest_ip = self.hosts.get_hosts(dest_host)
                        next_hop, src_name = self.get_nexthop(dest_ip, "")
                        print("[DEBUG] Dest ip", dest_ip)
                        print("[DEBUG] Next hop ip", next_hop)
                        print("[DEBUG] Next hop interface", src_name)

                        fd = self.iface2fd[src_name]
                        src_ip = self.iface[src_name].ip
                        src_mac = self.iface[src_name].mac

                        ip_packet = IPpacket(
                            msg_args[-1].replace("\n", ""), src_ip, dest_ip)

                        if next_hop in self.arp.table:
                            print("[DEBUG] Entry in ARP cache. Updating timer")
                            self.arp.reset_timer(next_hop)
                            dest_mac = self.arp.get(next_hop)
                            data_frame = DataFrame(
                                ip_packet, src_ip, dest_ip, src_mac, dest_mac)
                            encrypted_df = pickle.dumps(data_frame)
                            serialised_frame = pickle.dumps(
                                {"type": "dataframe", "data": encrypted_df})
                            print("[INFO] Sending dataframe of size {} bytes to {}".format(
                                len(serialised_frame), dest_mac))
                            fd.send(serialised_frame)
                        else:
                            print(
                                "[DEBUG] Entry not in ARP cache. Initialising ARP request.")
                            self.pq.table[next_hop].append(ip_packet)
                            print("Added IPpacket to queue.")
                            self.init_arp_request(
                                ip_packet, src_ip, src_mac, next_hop, fd)

                    elif msg_args[0] == "show":
                        cmd = msg_args[1].replace("\n", "")
                        if cmd.lower() == "hosts":
                            self.hosts.show()
                        elif cmd.lower() == "arp":
                            self.arp.show()
                        elif cmd.lower() == "pq":
                            self.pq.show()
                        elif cmd.lower() == "ifaces":
                            Interface.show_ifaces(self.iface)
                        elif cmd.lower() == "rtables":
                            RouteTable.show_rtables(self.rtable)
                        else:
                            print("[ERROR] INVALID REQUEST TO STATION")
                            print("AVAILABLE COMMANDS AT STATION")
                            print("- send destionation message")
                            print("- show pq or arp or ifaces or rtables or hosts")
                            print("- quit")

                    elif "quit" in msg_args[0]:
                        print("[INFO] Closing station")
                        for station_fd in self.fd2iface:
                            station_set.remove(station_fd)
                        sys.exit(0)

    def read_file(self, filename):
        """Read lines from each file and load to respective classes

        Args:
            filename (string): ifaces, rtables, hosts path 

        Returns:
            key value pair: dictionary or list containing respective class objects
        """
        metadata = {} if "iface" in filename else []
        with open(filename) as file:
            lines = file.readlines()
            for line in lines:
                parsed_line = [details.replace("\n", "").replace(
                    "\t", "") for details in line.split(" ") if details != ""]
                try:
                    if "iface" in filename and parsed_line != ['']:
                        if len(parsed_line) == 4:
                            parsed_line.insert(3, '')
                        iface = Interface(parsed_line)
                        # iface.show()
                        metadata[parsed_line[0]] = iface
                    elif parsed_line != ['']:
                        rtable = RouteTable(parsed_line)
                        # rtable.show()
                        metadata.append(rtable)
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
    """main method to start station
    """
    args = load_args()
    signal.signal(signal.SIGINT, handle_interupt)
    station = Station(args)
    station.initialize()


if __name__ == "__main__":
    main()
