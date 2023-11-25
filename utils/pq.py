"""
Authors:
- Sri Sai Ram Kiran Muppana
- [potato]
"""

from collections import defaultdict


class PQ:
    def __init__(self):
        self.table = defaultdict(list)

    def remove_entry(self, ip, packet):
        if ip in self.table:
            self.table[ip].remove(packet)
            if self.table[ip] == []:
                del self.table[ip]

    def show(self):
        print("+-----------------------------------+")
        print("|          PENDING QUEUE            |")
        print("+-----------------------------------+")
        print("|     next hop     | # PKTS Waiting |")
        print("+-----------------------------------+")
        for ip, value in self.table.items():
            print("| {:<16} | {:<14} |".format(ip, len(value)))
        print("+-----------------------------------+")
        print()

