import os

class Hosts:
    def __init__(self, filename):
        self.hosts = self.load_hosts(filename)
        self.print_hosts()
    
    def load_hosts(self, filename):
        hosts = {}
        with open(filename) as file:
            lines = file.readlines()
            for line in lines:
                parsed_line = [ details for details in line.replace("\n", " ").replace("\t"," ").split(" ") if details!= ""]
                if len(parsed_line) == 2:
                    hosts[parsed_line[0]] = parsed_line[1]
        return hosts
    
    def get_hosts(self):
        return self.hosts
    
    def print_hosts(self):
        print("[INFO] Available hosts: ")
        for host, ip in self.hosts.items():
            print(host, "\t", ip)
        
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
    msg = ""
    dll_src_ip = ""
    dll_src_mac = ""
    dll_dest_ip = ""
    dll_dest_mac = ""
    
    def __init__(self):
        pass
    
    def print_dataframe(self):
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
        pass
    
class SL:
    def __init__(self):
        pass
    
class PQ:
    def __init__(self):
        pass
        
# hosts = Hosts("./hosts")
# print(hosts.get_hosts())