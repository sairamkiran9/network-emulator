"""
Authors:
- Sri Sai Ram Kiran Muppana
- Sahithi Vungarala
"""

from collections import defaultdict


class PQ:
    """pending queue datastructure class
    """

    def __init__(self):
        self.table = defaultdict(list)  # empty dict init

    def remove_entry(self, ip, i):
        """removes entry of "ip" key at ith index

        Args:
            ip (string): key
            i (string): position of index
        """
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
