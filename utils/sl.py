"""
Authors:
- Sri Sai Ram Kiran Muppana
- [potato]
"""

import time
import threading


class SL:
    def __init__(self):
        self.table = {}
        self.timer_thread = threading.Thread(
            target=self.update_timer, daemon=True)
        self.timer_thread.start()

    def get(self, mac):
        entry = self.table.get(mac)
        if entry and entry["timer"] > 0:
            return entry["fd"]
        return ""

    def add_entry(self, mac, fd, port):
        self.table[mac] = {
            "fd": fd,
            "port": port,
            "timer": 60
        }

    def remove_entry(self, fd):
        key = ""
        for k,v in self.table.items():
            if v["fd"] == fd:
                key = k
                break
        if key:
            del self.table[key]
        
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

    def show(self):
        print("+-------------------------------------------+")
        print("|             SELF LEARNING TABLE           |")
        print("+-------------------------------------------+")
        print("|    MAC ADDRESS    |  PORT  |  FD  |  TTL  |")
        print("+-------------------------------------------+")

        for ip, value in self.table.items():
            print("| {:<17} | {:<6} | {:<4} | {:<5} |".format(
                ip, value["port"], value["fd"].fileno(), value["timer"]))
        print("+-------------------------------------------+")
        print()
