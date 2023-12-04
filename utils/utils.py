"""
Authors:
- Sri Sai Ram Kiran Muppana
- Sahithi Vungarala
"""

import sys
import time

class Interface:
    def __init__(self, params):
        self.name = params[0]
        self.ip = params[1]
        self.nwmask = params[2]
        self.mac = params[3]
        self.lanname = params[4]

    def show(self):
        print("""[DEBUG] Interface details:
            name \t- {} 
            ip \t\t- {}
            nwmask \t- {}
            mac \t- {}
            lan \t- {}
            """.format(self.name, self.ip, self.nwmask, self.mac, self.lanname))
      
    def show_ifaces(interfaces):
        print("+---------------------------------------------------------------------------+")
        print("|                             Interface Table                               |")
        print("+---------------------------------------------------------------------------+")
        print("|  Name  |    ip address   |      nwmask     |    mac address    | lan name |")
        print("+---------------------------------------------------------------------------+")

        for iface, value in interfaces.items():
            print("| {:<6} | {:<15} | {:<15} | {:<17} | {:<8} |".format(
                value.name, value.ip, value.nwmask, value.mac, value.lanname))
        print("+---------------------------------------------------------------------------+")
        print()
        


class DataFrame:
    def __init__(self, packet, src_ip, dest_ip, src_mac, dest_mac):
        self.packet = packet
        self.src_ip = src_ip
        self.dest_ip = dest_ip
        self.src_mac = src_mac
        self.dest_mac = dest_mac

    def show(self):
        print("""[DEBUG] DataFrame details:
            msg \t- {}
            src_ip \t- {}
            src_mac \t- {}
            dest_ip \t- {}
            dest_mac \t- {}
            """.format(self.msg, self.dll_src_ip,
                       self.dll_src_mac, self.dll_dest_ip, self.dll_dest_mac))


def handle_interupt(signal, frame):
    print("\n[INFO] Ctrl+C received. Closing Station.")
    time.sleep(1)
    sys.exit(0)