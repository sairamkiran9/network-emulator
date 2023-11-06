import os

class Interface:
    def __init__(self, params):
        self.name = params[0]
        self.ip = params[1]
        self.nwmask = params[2]
        self.mac = params[3]
        self.lanname = params[4]
        
    def print_interface(self):
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
        
    def print_routetable(self):
        print("""[DEBUG] Route table details:
            dest_ip \t- {}
            next_hop \t- {}
            nwmask \t- {}
            iface \t- {}
            """.format(self.dest_ip, self.next_hop, self.nwmask, self.iface))
        
class DataFrame:
    def __init__(self):
        pass
        
class ARP:
    def __init__(self):
        pass
    
class SL:
    def __init__(self):
        pass
    
class PQ:
    def __init__(self):
        pass
        
        