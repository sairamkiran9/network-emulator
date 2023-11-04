import os

class RouteTable:
    def __init__(self, params):
        self.dest_ip = params[0]
        self.next_hop = params[1]
        self.nwmask = params[2]
        self.iface = params[3]
        
    def print_routetable(self):
        print("""[DEBUG] Route table details:
            dest_ip \t- {}
            next_hop \t- {}
            nwmask \t- {}
            iface \t- {}
            """.format(self.dest_ip, self.next_hop, self.nwmask, self.iface))
        
# rtable = RouteTable(['128.252.13.64', '128.252.13.38', '255.255.255.224', 'C'])
# rtable.print_routetable()