class IpToTimeMap(object):
    def __init__(self):
        self.ip_to_time = {}

    def is_in(self, ip):
        return ip in self.ip_to_time
    def get_time(self, ip):
        return self.ip_to_time[ip]
    def store_time(self, ip, time):
        self.ip_to_time[ip] = time
