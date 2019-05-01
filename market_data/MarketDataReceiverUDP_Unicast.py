import json
import socket
import time
from threading import Thread

UDP_IP = socket.gethostbyname(socket.gethostname())
UDP_PORT = 5005
BUFFER_SIZE = 1024

# NETWORK ADDRESS OF THIS SERVER
server_address = (UDP_IP, UDP_PORT)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(server_address)


class MarketDataReceiver:

    def __init__(self, verbose: bool, f):
        print("Initialising Market Data Receiver")
        print(server_address)
        self.verbose = verbose
        self.place_order_fnc = f

        self.last_update = 0
        self.listener = Thread(name="MarketDataReceiver", target=self.__listen)

    def distribute(self, lob):
        self.place_order_fnc(lob)

    def run(self):
        self.listener.start()

    def __listen(self):
        print("Listening...")
        while True:
            msg, address = sock.recvfrom(BUFFER_SIZE)

            lob_update = json.loads(msg.decode('utf-8'))

            if lob_update["time"] > self.last_update:

                if self.verbose:
                    # print("MARKET UPDATE")
                    # self.__print_lob(lob_update)
                    self.__print_stats(lob_update)

                self.distribute(lob_update)
                self.last_update = lob_update["time"]

    def __print_lob(self, lob_update):
        print("LOB: " + str(lob_update))

    def __print_stats(self, lob_update):
        now = time.time()
        print("%.1f" % ((now - lob_update["time"]) * 1000))
        # print("Latency = %.1fms (NOW=%f SENT=%f)" % ((now - lob_update["time"]) * 1000, now, lob_update["time"]))
        # print("Time Since Last = %f\n" % (lob_update['time'] - self.lob['time']))
