import socket, json
from threading import Thread
from datetime import datetime

UDP_IP = socket.gethostbyname(socket.gethostname())
UDP_PORT = 5005
BUFFER_SIZE = 1024

# NETWORK ADDRESS OF THIS SERVER
server_address = (UDP_IP, UDP_PORT)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(server_address)


class MarketDataReceiver:

    def __init__(self, verbose: bool):
        print("Initialising Market Data Receiver")
        print(server_address)
        self.lob = {}
        self.verbose = verbose
        Thread(target=self.__listen).start()

    def get_lob(self):
        return self.lob

    def __listen(self):
        print("Listening...")
        while True:
            msg, address = sock.recvfrom(BUFFER_SIZE)

            lob_update = json.loads(msg.decode('utf-8'))
            if self.lob != {} and self.verbose:
                self.__print_update(lob_update)

            self.lob = lob_update

    def __print_update(self, lob_update):
        print("\nMARKET UPDATE: %s" % lob_update)
        print("Latency = %f" % (datetime.timestamp(datetime.now()) - lob_update['time']))
        print("Time Since Last = %f\n" % (lob_update['time'] - self.lob['time']))

