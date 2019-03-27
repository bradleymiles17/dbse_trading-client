import socket, struct, json, time
from threading import Thread

# REMOTE GROUP IP
multicast_group = '224.3.29.71'

# NETWORK ADDRESS OF THIS SERVER
server_address = ('192.168.0.17', 10000)

# Create the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind to the server address
sock.bind(server_address)


group = socket.inet_aton(multicast_group)
mreq = struct.pack('4sL', group, socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)


class MarketDataReceiver:

    def __init__(self):
        print("Initialising Market Data Receiver")
        self.lob = {}
        Thread(target=self.listen).start()

    def listen(self):
        print("Listening...")
        while True:
            bytes, address = sock.recvfrom(1024)

            new_lob = json.loads(bytes.decode('utf-8'))
            if self.lob == {}:
                self.lob = new_lob

            print("\n")
            print("MARKET UPDATE: %s" % new_lob)
            print("Latency = %f" % (time.time() - new_lob['time']))
            print("Last = %f" % (new_lob['time'] - self.lob['time']))
            print("\n")
            self.lob = new_lob

    def get_lob(self):
        return self.lob
