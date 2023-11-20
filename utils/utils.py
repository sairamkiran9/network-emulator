"""
Utils.py: The main functionality of bridge
Authors:
- Sri Sai Ram Kiran Muppana
- [potato]
"""

import time
import pickle
import threading
from collections import defaultdict


class Hosts:
    hosts = {}
    def __init__(self, filename):
        with open(filename) as file:
            lines = file.readlines()
            for line in lines:
                parsed_line = [details for details in line.replace(
                    "\n", " ").replace("\t", " ").split(" ") if details != ""]
                if len(parsed_line) == 2:
                    self.hosts[parsed_line[0]] = parsed_line[1]

    def get_hosts(self, name):
        return self.hosts[name]

    def show(self):
        print("+-----------------------------------+")
        print("|            DNS TABLE              |")
        print("+-----------------------------------+")
        print("|    HOSTNAME     |    IP Address   |")
        print("+-----------------------------------+")

        for host, ip in self.hosts.items():
            print("| {:^15} | {:^15} |".format(host, ip))
        print("+-----------------------------------+")
        print()


class Interface:
    def __init__(self, params):
        self.name = params[0]
        self.ip = params[1]
        self.nwmask = params[2]
        self.mac = params[3]
        self.lanname = params[4]

    def show(self):
        print("""[DEBUG] Interface details:
            name \t- {} 
            ip \t\t- {}
            nwmask \t- {}
            mac \t- {}
            lan \t- {}
            """.format(self.name, self.ip, self.nwmask, self.mac, self.lanname))


class RouteTable:
    def __init__(self, params):
        self.dest_ip = params[0]
        self.next_hop = params[1]
        self.nwmask = params[2]
        self.iface = params[3]

    def route(self, ip):
        dest_ip = ''.join(format(int(x), '08b') for x in ip.split('.'))
        bin_subnet = ''.join(format(int(x), '08b')
                             for x in self.nwmask.split('.'))
        bin_next_prefix = ''.join(str(int(a) & int(b))
                             for a, b in zip(dest_ip, bin_subnet))
        next_prefix = '.'.join(
            str(int(bin_next_prefix[i:i+8], 2)) for i in range(0, 32, 8))
        if self.dest_ip == next_prefix or next_prefix == "0.0.0.0":
            return self.next_hop
        return ""

    def show(self):
        print("""[DEBUG] Route table details:
            dest_ip \t- {}
            next_hop \t- {}
            nwmask \t- {}
            iface \t- {}
            """.format(self.dest_ip, self.next_hop, self.nwmask, self.iface))


class DataFrame:
    def __init__(self, packet, src_ip, dest_ip, src_mac, dest_mac):
        self.packet = packet
        self.src_ip = src_ip
        self.dest_ip = dest_ip
        self.src_mac = src_mac
        self.dest_mac = dest_mac

    def show(self):
        print("""[DEBUG] DataFrame details:
            msg \t- {}
            src_ip \t- {}
            src_mac \t- {}
            dest_ip \t- {}
            dest_mac \t- {}
            """.format(self.msg, self.dll_src_ip,
                       self.dll_src_mac, self.dll_dest_ip, self.dll_dest_mac))


class ARP:
    def __init__(self):
        self.table = {}
        self.timer_thread = threading.Thread(
            target=self.update_timer, daemon=True)
        self.timer_thread.start()

    def get(self, ip):
        entry = self.table.get(ip)
        if entry and entry["timestamp"] > 0:
            return entry["mac"]
        return ""

    def add_entry(self, ip, mac):
        self.table[ip] = {
            "mac": mac,
            "timestamp": 60
        }

    def update_timer(self):
        while True:
            keys = []
            for key in self.table:
                if self.table[key]["timestamp"] > 0:
                    self.table[key]["timestamp"] -= 1
                else:
                    keys.append(key)
            time.sleep(1)
            for ip in keys:
                print("[DEBUG] One entry in arp cache timed out")
                del self.table[ip]

    def request(self, src_ip, dest_ip, src_mac, dest_mac="FF:FF:FF:FF"):
        arp_request = {
            "type": "arp_request",
            "src_ip": src_ip,
            "src_mac": src_mac,
            "dest_ip": dest_ip,
            "dest_mac": dest_mac,
        }
        encrypted_frame = pickle.dumps(arp_request)
        return encrypted_frame

    def reply(self, data):
        arp_reply = {
            "type": "arp_reply",
            "src_ip": data["dest_ip"],
            "src_mac": data["dest_mac"],
            "dest_ip": data["src_ip"],
            "dest_mac": data["src_mac"]
        }
        encrypted_frame = pickle.dumps(arp_reply)
        return encrypted_frame

    def show(self):
        if self.table:
            print(self.table)
        else:
            print({})


class SL:
    def __init__(self):
        self.table = {}
        self.timer_thread = threading.Thread(
            target=self.update_timer, daemon=True)
        self.timer_thread.start()
        
    def get(self, mac):
        entry = self.table.get(mac)
        if entry and entry["timestamp"] > 0:
            return entry["fd"]
        return "" ## what if entry is removed from SL table?

    def add_entry(self, mac, fd, port):
        self.table[mac] = {
            "fd": fd,
            "port": port,
            "timestamp": 60
        }

    def update_timer(self):
        while True:
            keys = []
            for key in self.table:
                if self.table[key]["timestamp"] > 0:
                    self.table[key]["timestamp"] -= 1
                else:
                    keys.append(key)
            time.sleep(1)
            for ip in keys:
                del self.table[ip]

    def show(self):
        print("+-------------------------------------------+")
        print("|             SELF LEARNING TABLE           |")
        print("+-------------------------------------------+")
        print("|    MAC ADDRESS    |  PORT  |  FD  |  TTL  |")
        print("+-------------------------------------------+")

        for ip, value in self.sl.table.items():
            print("| {:^17} | {:^6} | {:^4} | {:^5} |".format(ip, value["port"], value["fd"], value["timestamp"]))
        print("+-------------------------------------------+")
        print()


class PQ:
    def __init__(self):
        self.table = defaultdict(list)
        
    def remove_entry(self, ip):
        if ip in self.table:
            self.table[ip].pop(0)
            if self.table[ip] == []:
                del self.table[ip]

    def show(self):
        print("+-------------------------------------+")
        print("|           PENDING QUEUE             |")
        print("+-------------------------------------+")
        print("|       DEST IP      | # PKTS Waiting |")
        print("+-------------------------------------+")
        for ip, value in self.pq.items():
            print("| {:^20} | {:^20} |".format(ip, len(value)))
        print("+-------------------------------------+")
        print()

class IPpacket:
    def __init__(self, msg, src_ip, dest_ip):
        self.msg = msg
        self.src_ip = src_ip
        self.dest_ip = dest_ip

    def show(self):
        print("+---------------------------------------------------------+")
        print("|                        IP PACKET                        |")
        print("+---------------------------------------------------------+")
        print("|     MESSAGE     |       SRC IP      |      DEST IP      |")
        print("+---------------------------------------------------------+")
        print("| {:^15} | {:^17} | {:^17} |".format(self.msg, self.src_ip, self.dest_ip))
        print("+---------------------------------------------------------+")
        print()
