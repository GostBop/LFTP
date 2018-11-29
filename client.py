# -*- coding=utf-8 -*-
from __future__ import print_function
from socket import *
import pickle, random, threading, time, os, sys, Queue

# ----------------------------------------------

class c_pkt(object):
    # packet with sequence number and data
    def __init__(self, seq, data):
        self.seq = seq
        self.data = data

class s_pkt(object):
    # packet with rwnd and ack
    def __init__(self, rwnd, ack):
        self.rwnd = rwnd
        self.ack = ack

# ----------------------------------------------

serverName = '127.0.0.1'
serverPort = 12000
server_addr = (serverName, serverPort)

DATA_SIZE = 1024
BUF_SIZE = 65535
time_limit = 0.001

filePath = 'C:\Users\Sandman\Desktop\\test.jpg'
fsize = os.path.getsize(filePath)
num_of_times = fsize / DATA_SIZE
print('num_of_times : %d' % num_of_times)

windows = Queue.Queue()
N = 3000
base = 0
next_seq_num = 0
seq_limit = 10000

timers = dict()
seqs = dict()

count = 0
start = 0
end = 0

LastByteSent = 0
LastByteAcked = -1
rwnd = 1
my_rwnd = 1
sent_but_not_acked = 0

# ----------------------------------------------

def progress(percent,width = 50):
	show_str = ('[%%-%ds]' % width) % (int(width * percent / 100) * "#")
	print('\r%s %d%%' % (show_str, percent), end = '')

def calculate_rwnd(LastByteRcvd, LastByteRead, RcvBuffer, rwnd):
    buffer = LastByteRcvd - LastByteRead
    if buffer < 0 and -buffer > RcvBuffer:
        buffer = RcvBuffer + buffer 
    rwnd = RcvBuffer - buffer
    return buffer

def start_timer(seq, data):
    timers[seq] = threading.Timer(time_limit, send_pkt, (seq, data))
    timers[seq].start()

def send_pkt(seq, data):
    clientSocket.sendto(pickle.dumps(c_pkt(seq, data)), server_addr)
    LastByteSent = seq
    start_timer(seq, data)

def send_if_rwnd():
    clientSocket.sendto('', server_addr)

def rcv():
    global f, count, num_of_times, start, rwnd, end, base, seqs, windows
    global sent_but_not_acked, LastByteAcked, LastByteSent, seq_limit
    while True:
        if start == 0:
            continue

        while base in seqs:
            if seqs[base] == 1:
                LastByteAcked = base
                windows.get()
                base = (base + 1) % seq_limit
            else:
                break

        response, server_addr = clientSocket.recvfrom(BUF_SIZE)
        server_pkt = pickle.loads(response)
        rwnd = server_pkt.rwnd
        if rwnd == 0:
            continue
        
        sent_but_not_acked = calculate_rwnd(LastByteSent, LastByteAcked, N, my_rwnd)

        if sent_but_not_acked > rwnd:
            continue

        if server_pkt.ack == 'exit':
            count = num_of_times
            progress(100 * count / num_of_times)
            print(' done!') # timerÊÇ·ñÈ«²¿cancel?
            f.close()
            clientSocket.close()
            print('closed')
            break
        else:
            seq = int(server_pkt.ack)
            # [down_to_ack, up_to_ack)
            up_to_ack = (seq + 1) % seq_limit
            down_to_ack = (LastByteAcked + 1) % seq_limit
            if up_to_ack > down_to_ack:
                count = count + up_to_ack - down_to_ack
                for i in range(down_to_ack, up_to_ack):
                    timers[i].cancel()
                    seqs[i] = 1
            elif up_to_ack < down_to_ack:
                count = count + up_to_ack + seq_limit + 1 - down_to_ack
                for i in range(0, up_to_ack):
                    timers[i].cancel()
                    seqs[i] = 1
                for i in range(down_to_ack, seq_limit + 1):
                    timers[i].cancel()
                    seqs[i] = 1
            LastByteAcked = seq
            progress(100 * count / num_of_times)

          
def transmit_windows():
    global next_seq_num, base, start, sent_but_not_acked
    while True: 
        if rwnd == 0:
            print('wait...')
            # time.sleep(1)
            send_if_rwnd()
        elif sent_but_not_acked > rwnd:
            print('wait.')
            continue
        elif my_rwnd > 0:
            data = f.read(DATA_SIZE)
            if data:
                windows.put(data)
                seqs[next_seq_num] = 0
                send_pkt(next_seq_num, data)
                start = 1
                next_seq_num = (next_seq_num + 1) % seq_limit
            else:
                clientSocket.sendto('exit', server_addr)
                break
            
                
# ----------------------------------------------

clientSocket = socket(AF_INET, SOCK_DGRAM)
f = open(filePath, 'rb')

clientSocket.sendto(str(num_of_times), server_addr)

t = threading.Thread(target = rcv)
# t.daemon = True
t.start()

transmit_windows()

t.join()

