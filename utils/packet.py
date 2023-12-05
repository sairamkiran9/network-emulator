"""
Authors:
- Sri Sai Ram Kiran Muppana
- Sahithi Vungarala
"""


class IPpacket:
    """IPpacket datastructure class
    """

    def __init__(self, msg, src_ip, dest_ip):
        self.msg = msg
        self.src_ip = src_ip
        self.dest_ip = dest_ip

    def show(self):
        print("+---------------------------------------------------------+")
        print("|                        IP PACKET                        |")
        print("+---------------------------------------------------------+")
        print("|     MESSAGE     |       SRC IP      |      DEST IP      |")
        print("+---------------------------------------------------------+")
        print("| {:<15} | {:<17} | {:<17} |".format(
            self.msg, self.src_ip, self.dest_ip))
        print("+---------------------------------------------------------+")
        # print()
