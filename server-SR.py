from socket import *
import pickle
import time

class pkt(object):
    # packet with sequence number and data
    def __init__(self, seq, data):
        self.seq = seq
        self.data = data

# ----------------------------------------------

serverName = '127.0.0.1'
serverPort = 12000
server_addr = (serverName, serverPort)

filePath = 'C:\Users\Sandman\Desktop\\test-copy.mp4'

DATA_SIZE = 1024
BUF_SIZE = 65535

windows = dict()
N = 20
base = 0

reqs = dict()

# ----------------------------------------------

serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(server_addr)
print "The server is ready to receive"

f = open(filePath, 'wb')

while True:
    #print('want to recv...')
    data, client_addr = serverSocket.recvfrom(BUF_SIZE)
    #print('anlyse the data...')
    if data == 'exit':
        serverSocket.sendto('exit', client_addr)
        print 'done!'
        break
    else:
        client_pkt = pickle.loads(data)
        #if (client_pkt.seq - base + 1000) % 1000 < N:
        windows[client_pkt.seq] = client_pkt.data
        serverSocket.sendto(str(client_pkt.seq), client_addr)
        reqs[client_pkt.seq] = 1
        while base in reqs and reqs[base] == 1:
            f.write(windows[base])
            reqs[base] = 0
            base = (base + 1) % 1000
f.close()
serverSocket.close()