"""
Authors:
- Sri Sai Ram Kiran Muppana
- [potato]
"""

from collections import defaultdict


class PQ:
    def __init__(self):
        self.table = defaultdict(list)

    def remove_entry(self, ip, i):
        if ip in self.table:
            self.table[ip].pop(i)
            if self.table[ip] == []:
                del self.table[ip]

    def show(self):
        print("+"+("="*57)+"+")
        print("| {:^55} |".format("PENDING QUEUE"))
        print("+"+("="*57)+"+")
        print("| {:^26} | {:^26} |".format("next hop", "# PKTS Waiting"))
        for ip, value in self.table.items():
            print("+"+("="*57)+"+")
            print("| {:^26} | {:^26} |".format(ip, len(value)))
            print("+"+("="*57)+"+")
            for packet in value:
                packet.show()
        print("+"+("="*57)+"+")
        print()

