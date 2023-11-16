"""
station.py: The main functionality of station and router
Authors:
- Sri Sai Ram Kiran Muppana
- [potato]
"""

import sys
import socket
import select
import pickle
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
        self.hosts = Hosts(params[4])
        self.hosts.show()

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

    def get_nexthop(self, ip):
        next_hop = ""
        for lan in self.rtable:
            next_hop = self.rtable[lan].route(ip)
            if next_hop != "" and next_hop != "0.0.0.0":
                return next_hop
        if next_hop == "":
            for lan in self.rtable:
                details = self.rtable[lan]
                if details.dest_ip == "0.0.0.0":
                    print("[INFO] Default gateway router")
                    return details.next_hop
                
        return ip

    def init_arp_request(self, encapsulated_packet, src_ip, src_mac, next_hop, fd):
        arp_request = self.arp.request(src_ip, next_hop, src_mac)
        print("[DEBUG] Sending arp request of size {} bytes through {}".format(
            len(arp_request), self.fd2iface[fd]))
        fd.send(arp_request)

    def initialize(self):
        client_set = set()
        client_set.add(sys.stdin)

        for iface_name in self.iface:
            print("[INFO] Initializing interface ", iface_name)
            cur_iface = self.iface[iface_name]
            bridge_ip, port = self.get_landetails(cur_iface.lanname)

            hints = socket.getaddrinfo(
                bridge_ip, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
            for addr in hints:
                try:
                    sockfd = socket.socket(addr[0], addr[1], addr[2])
                    station_ip = self.hosts.get_hosts(iface_name)
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

            addr_info = sockfd.getsockname()
            ipstr = addr_info[0]
            port = addr_info[1]
            print("[DEBUG] Bridge accepted iface {} on '{}' at '{}' thru '{}'".format(
                iface_name, ipstr, bridge_ip, port))
            client_set.add(sockfd)

        while True:
            temp_set, _, _ = select.select(client_set, [], [])
            for r in temp_set:
                if r in client_set and r != sys.stdin:
                    response = r.recv(4096)

                    if not response:
                        print("Bridge disconnected.")
                        sys.exit(0)

                    cur_iface = self.fd2iface[r]
                    data = pickle.loads(response)

                    if data["type"] == "arp_request":
                        if data["dest_ip"] == self.hosts.get_hosts(cur_iface):
                            print(
                                "[DEBUG] It's My IP sending back ARP response.")
                            data["dest_mac"] = self.iface[cur_iface].mac
                            arp_reply = self.arp.reply(data)
                            r.send(arp_reply)

                    elif data["type"] == "arp_reply":
                        src_ip, src_mac, dest_ip, dest_mac = data["dest_ip"], data[
                            "dest_mac"], data["src_ip"], data["src_mac"]
                        print("[DEBUG] Received arp response of size {} bytes from {}".format(
                            len(data), dest_ip))
                        self.arp.add_entry(dest_ip, dest_mac)
                        # print("[DEBUG] Cuurent pending queue entries ", self.pq.table.keys())
                        # print("\n\n")
                        if dest_ip in self.pq.table:
                            packets = self.pq.table[dest_ip]
                            for packet in packets:
                                data_frame = DataFrame(
                                    packet, src_ip, dest_ip, src_mac, dest_mac)
                                encrypted_df = pickle.dumps(data_frame)
                                serialised_frame = pickle.dumps(
                                    {"type": "dataframe", "data": encrypted_df})
                                print("[DEBUG] Sending dataframe to ", dest_ip)
                                print("len of pq before: ", len(self.pq.table[dest_ip]))
                                self.pq.table[dest_ip].pop(0)
                                r.send(serialised_frame)
                                print("len of pq after: ", len(self.pq.table[dest_ip]))
                        else:
                            print(
                                "[DEBUG] Got ARP response but pending queue is empty. Nothing to forward.")

                    elif data["type"] == "dataframe":
                        data_frame = pickle.loads(data["data"])
                        if data_frame.dest_mac == self.iface[cur_iface].mac:
                            ip_packet = pickle.loads(data_frame.packet)
                            if ip_packet.dest_ip == self.iface[cur_iface].ip:
                                ip_packet.show()
                                print("[INFO] Received frame of size {} bytes".format(
                                    len(data["data"])))
                                print("{} >> {}".format(
                                    cur_iface, ip_packet.msg))
                            else:
                                self.arp.add_entry(
                                    self.iface[cur_iface].ip, data_frame.dest_mac)
                                print("[DEBUG] Entry not in ARP cache. Initialising ARP request.")
                                next_hop = self.get_nexthop(ip_packet.dest_ip)
                                print("[DEBUG] Going for next hop", next_hop)
                                self.pq.table[next_hop].append(data_frame.packet)
                                print("pending queue in dataframe ", self.pq.table.keys())
                                # for key in self.ip2fd.keys():
                                self.init_arp_request(
                                    data_frame.packet, self.iface[cur_iface].ip, self.iface[cur_iface].mac, ip_packet.dest_ip, r)

                elif r == sys.stdin:
                    msg = sys.stdin.readline()
                    if not msg:
                        sys.exit(0)
                    msg_args = msg.split(" ", 1)
                    if msg_args[0] == "send":
                        msg_args = msg.split(" ", 2)
                        dest_host = msg.split(" ")[1]
                        if dest_host not in self.hosts.hosts:
                            print("[ERROR] Unrecognised host.",
                                  dest_host, " not in DNS")
                        dest_ip = self.hosts.get_hosts(dest_host)
                        for src_name, fd in self.iface2fd.items():
                            src_ip = self.iface[src_name].ip
                            src_mac = self.iface[src_name].mac
                            ip_packet = IPpacket(
                                msg_args[-1].replace("\n", ""), src_ip, dest_ip)
                            encapsulated_packet = pickle.dumps(ip_packet)
                            if dest_ip in self.arp.table:
                                print("[DEBUG] Entry in ARP cache")
                                dest_mac = self.arp.get(dest_ip)
                                data_frame = DataFrame(
                                    encapsulated_packet, src_ip, dest_ip, src_mac, dest_mac)
                                encrypted_df = pickle.dumps(data_frame)
                                serialised_frame = pickle.dumps(
                                    {"type": "dataframe", "data": encrypted_df})
                                print("[INFO] Sending dataframe of size {} bytes".format(
                                    len(serialised_frame)))
                                if dest_ip in self.pq.table:
                                    self.pq.table["dest_ip"].pop(0) # need to change this because packet always can't be at the start
                                fd.send(serialised_frame)
                            else:
                                print("[DEBUG] Entry not in ARP cache. Initialising ARP request.")
                                next_hop = self.get_nexthop(dest_ip)
                                print("[DEBUG] Next hop address", next_hop)
                                self.pq.table[next_hop].append(encapsulated_packet)
                                self.init_arp_request(
                                    encapsulated_packet, src_ip, src_mac, next_hop, fd)

                    elif msg_args[0] == "show":
                        cmd = msg_args[1].replace("\n", "")
                        if cmd == "hosts":
                            # create a good printing format - [potato]
                            self.hosts.show()
                        elif cmd == "arp":
                            # create a good printing format - [potato]
                            self.arp.show()
                        elif cmd == "pq":
                            # create a good printing format - [potato]
                            self.pq.show()
                        else:
                            print("[ERROR] INVALID REQUEST TO STATION")
                            print("AVAILABLE COMMANDS AT STATION")
                            # print all the list of functions - [potato]

    def read_file(self, filename):
        metadata = {}
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
                        iface.show()
                        metadata[parsed_line[0]] = iface
                    elif parsed_line != ['']:
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
