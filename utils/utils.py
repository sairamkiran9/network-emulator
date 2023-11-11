import os
import time
import pickle
from collections import defaultdict

class Hosts:
    def __init__(self, filename):
        self.hosts = self.load_hosts(filename)
        self.show()

    def load_hosts(self, filename):
        hosts = {}
        with open(filename) as file:
            lines = file.readlines()
            for line in lines:
                parsed_line = [details for details in line.replace(
                    "\n", " ").replace("\t", " ").split(" ") if details != ""]
                if len(parsed_line) == 2:
                    hosts[parsed_line[0]] = parsed_line[1]
        return hosts
    
    def get_hosts(self):
        return self.hosts

    def show(self):
        print("[DEBUG] Available hosts: ")
        for host, ip in self.hosts.items():
            print(host, "\t", ip)
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

    def show(self):
        print("""[DEBUG] Route table details:
            dest_ip \t- {}
            next_hop \t- {}
            nwmask \t- {}
            iface \t- {}
            """.format(self.dest_ip, self.next_hop, self.nwmask, self.iface))


class DataFrame:
    def __init__(self, packet, src_mac, dest_mac):
        self.packet = packet
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
    def __init__(self, timeout=60):
        self.table = {}
        self.timeout = timeout

    def get(self, ip):
        entry = self.table.get(ip)
        # if entry and time.time() - entry["timestamp"] <= self.timeout:
        #     return entry["mac"]
        # return ""
        return entry
    
    def add_entry(self, ip, mac):
        self.table[ip] = {
            "mac": mac,
            "timestamp": time.time()
        }
        
    def remove_expired_entries(self):
        curr_time = time.time()
        expired_entries = [ip for ip, entry in self.table.items() if curr_time - entry["timestamp"] > self.timeout]
        for ip in expired_entries:
            del self.tabel[ip]
        
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
        print(self.table)


class SL:
    def __init__(self):
        self.table = {}

    def show(self):
        print(self.table)


class PQ:
    def __init__(self):
        self.table = defaultdict(list)

    def show(self):
        print(self.table)


class IPpacket:
    def __init__(self, msg, src_ip, dest_ip):
        self.msg = msg
        self.src_ip = src_ip
        self.dest_ip = dest_ip

    def show(self):
        print("""[DEBUG] Packet details:
            msg \t- {}
            src_ip \t- {}
            dest_ip \t- {}
            """.format(self.msg, self.src_ip, self.dest_ip))

