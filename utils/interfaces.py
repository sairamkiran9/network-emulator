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
        
# iface = Interface(['Acs1', '128.252.11.23', '255.255.255.0', '00:00:0C:04:52:27', 'cs1'])
# iface.print_interface()