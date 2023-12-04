"""
Authors:
- Sri Sai Ram Kiran Muppana
- Sahithi Vungarala
"""

import time
import pickle
import threading

class ARP:
    def __init__(self):
        self.table = {}
        self.timer_thread = threading.Thread(
            target=self.update_timer, daemon=True)
        self.timer_thread.start()

    def get(self, ip):
        entry = self.table.get(ip)
        if entry and entry["timer"] > 0:
            return entry["mac"]
        return ""

    def add_entry(self, ip, mac):
        self.table[ip] = {
            "mac": mac,
            "timer": 60
        }

    def update_timer(self):
        while True:
            keys = []
            for key in self.table:
                if self.table[key]["timer"] > 0:
                    self.table[key]["timer"] -= 1
                else:
                    keys.append(key)
            time.sleep(1)
            for ip in keys:
                print("[DEBUG] One entry in arp cache timed out")
                del self.table[ip]
                
    def reset_timer(self, ip):
        if ip in self.table:
            self.table[ip]["timer"] = 60

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
        print("+---------------------------------------------+")
        print("|                  ARP CACHE                  |")
        print("+---------------------------------------------+")
        print("|    IP ADDRESS   |    MAC ADDRESS    |  TTL  |")
        print("+---------------------------------------------+")

        for ip, value in self.table.items():
            print("| {:<15} | {:<17} | {:<5} |".format(
                ip, value["mac"], value["timer"]))
        print("+---------------------------------------------+")
        print()

