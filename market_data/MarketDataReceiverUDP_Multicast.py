import socket, struct, json
from threading import Thread
from datetime import datetime

# REMOTE GROUP IP
multicast_group = '224.3.29.71'

UDP_IP = socket.gethostname()
UDP_PORT = 10000
BUFFER_SIZE = 1024

# NETWORK ADDRESS OF THIS SERVER
server_address = (UDP_IP, UDP_PORT)

# Create the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind to the server address
sock.bind(server_address)


group = socket.inet_aton(multicast_group)
mreq = struct.pack('4sL', group, socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)


class MarketDataReceiver:

    def __init__(self, verbose: bool):
        print("Initialising Market Data Receiver")
        self.lob = {}
        self.verbose = verbose

    def get_lob(self):
        return self.lob

    def run_until(self, close_time):
        Thread(target=self.__listen, args=[close_time]).start()

    def __listen(self, close_time):
        print("Listening...")
        while datetime.now() < close_time:
            msg, address = sock.recvfrom(BUFFER_SIZE)

            lob_update = json.loads(msg.decode('utf-8'))
            if self.lob != {} and self.verbose:
                self.__print_update(lob_update)

            self.lob = lob_update

    def __print_update(self, lob_update):
        print("\nMARKET UPDATE: %s" % lob_update)
        print("Latency = %f" % (datetime.timestamp(datetime.now()) - lob_update['time']))
        print("Time Since Last = %f\n" % (lob_update['time'] - self.lob['time']))

