"""
Authors:
- Sri Sai Ram Kiran Muppana
- Sahithi Vungarala
"""

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

    def show_rtables(rtables):
        print("+---------------------------------------------------------------+")
        print("|                         Route Table                           |")
        print("+---------------------------------------------------------------+")
        print("|     dest ip    |    next hop    |      nwmask       |  iface  |")
        print("+---------------------------------------------------------------+")

        for value in rtables:
            print("| {:<14} | {:<14} | {:<17} | {:<7} |".format(
                value.dest_ip, value.next_hop, value.nwmask, value.iface))
        print("+---------------------------------------------------------------+")
        print()
