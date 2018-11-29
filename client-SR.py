# -*- coding=utf-8 -*-
from __future__ import print_function
from socket import *
import pickle, random, threading, time, os, sys, Queue

# ----------------------------------------------

class pkt(object):
    # packet with sequence number and data
    def __init__(self, seq, data):
        self.seq = seq
        self.data = data

# ----------------------------------------------

serverName = '127.0.0.1'
serverPort = 12000
server_addr = (serverName, serverPort)

DATA_SIZE = 1024
BUF_SIZE = 65535
time_limit = 3

filePath = 'C:\Users\Sandman\Desktop\\test.mp4'
fsize = os.path.getsize(filePath)
num_of_times = fsize / DATA_SIZE

# windows = Queue.Queue()
N = 20
base = 0
next_seq_num = 0

timers = dict()
seqs = dict()

count = 0
start = 0

# ----------------------------------------------

def progress(percent,width = 50):
	if percent >= 100:
		percent = 100
	show_str = ('[%%-%ds]' % width) % (int(width * percent / 100) * "#")
	print('\r%s %d%%' % (show_str, percent), end = '')

def start_timer(seq, data):
    global timers
    #print('chongchuan %d' % seq)
    timers[seq] = threading.Timer(time_limit, send_pkt, (seq, data))
    timers[seq].start()

def send_pkt(seq, data):
    clientSocket.sendto(pickle.dumps(pkt(seq, data)), server_addr)
    start_timer(seq, data)

def rcv():
    global count, num_of_times, start, base
    while True:
        if start == 0:
            continue
        response, server_addr = clientSocket.recvfrom(BUF_SIZE)
        count = count + 1
        progress(100 * count / num_of_times)
        print(response)
        if response == 'exit':
            break
        seq = int(response)
        timers[seq].cancel()
        seqs[seq] = 1
        while base in seqs:
            if seqs[base] == 1:
                # windows.get()
                base = (base + 1) % 1000
            else:
                break
          
def transmit_windows():
    global next_seq_num, base, start
    while True:
        if (next_seq_num - base + 1000) % 1000 < N:
            data = f.read(DATA_SIZE)
            if data:
                # windows.put(data)
                seqs[next_seq_num] = 0
                send_pkt(next_seq_num, data)
                start = 1
                next_seq_num = (next_seq_num + 1) % 1000
            else:
                clientSocket.sendto('exit', server_addr)
                break

                
# ----------------------------------------------

clientSocket = socket(AF_INET, SOCK_DGRAM)
f = open(filePath, 'rb')

t = threading.Thread(target = rcv)
t.start()

transmit_windows()

t.join()

f.close()
clientSocket.close()

