"""
Authors:
- Sri Sai Ram Kiran Muppana
- Sahithi Vungarala
"""


class Hosts:
    """Hosts dict

    Returns:
        dict: key value pairs of DNS
    """
    hosts = {}

    def __init__(self, filename):
        with open(filename) as file:
            lines = file.readlines()
            for line in lines:
                parsed_line = [details for details in line.replace(
                    "\n", " ").replace("\t", " ").split(" ") if details != ""]
                if len(parsed_line) == 2:
                    self.hosts[parsed_line[0]] = parsed_line[1]

    def get_hosts(self, name):
        return self.hosts[name]

    def show(self):
        print("+-----------------------------------+")
        print("|            DNS TABLE              |")
        print("+-----------------------------------+")
        print("|    HOSTNAME     |    IP Address   |")
        print("+-----------------------------------+")

        for host, ip in self.hosts.items():
            print("| {:<15} | {:<15} |".format(host, ip))
        print("+-----------------------------------+")
        print()
