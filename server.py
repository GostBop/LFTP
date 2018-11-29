# -*- coding=utf-8 -*-
from __future__ import print_function
from socket import *
import pickle, threading, time

# ----------------------------------------------
'''
    classes
'''

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
'''
    values
'''

serverName = '127.0.0.1'
serverPort = 12000
server_addr = (serverName, serverPort)

filePath = 'C:\Users\Sandman\Desktop\\test_copy.jpg'

DATA_SIZE = 1024
BUF_SIZE = 65535

windows = dict()
seqs = dict()

seq_limit = 10000
RcvBuffer = 3000
LastByteRead = -1
LastByteRcvd = -1
rwnd = 3000
num_of_times = -1
count = 0

done = 0

# ----------------------------------------------
'''
    functions
'''

def progress(percent,width = 50):
	show_str = ('[%%-%ds]' % width) % (int(width * percent / 100) * "#")
	print('\r%s %d%%' % (show_str, percent), end = '')

def file_write():
    global LastByteRead, f, num_of_times, count
    while True:
        if num_of_times == -1:
            break

        if done == 1 and count >= num_of_times:
            time.sleep(10)
            f.close()
            serverSocket.close()
            print('closed')
            break
        
        ByteToRead = (LastByteRead + 1) % seq_limit
        if ByteToRead in seqs and seqs[ByteToRead] == 1:
            # print('w %d to f' % ByteToRead)
            f.write(windows[ByteToRead])
            windows[ByteToRead] = ''
            count = count + 1
            progress(100 * count / num_of_times)
            seqs[ByteToRead] = 0
            LastByteRead = ByteToRead
            if count == num_of_times:
                break
        else:
            # if ByteToRead in seqs:
            #     print('seqs[%d]: %d' % (ByteToRead, seqs[ByteToRead]))
            # else:
            #     print('no entry: %d' % ByteToRead)
            break

def calculate_rwnd(LastByteRcvd, LastByteRead, RcvBuffer, rwnd):
    buffer = LastByteRcvd - LastByteRead
    if buffer < 0 and -buffer > RcvBuffer:
        buffer = RcvBuffer + buffer 
    rwnd = RcvBuffer - buffer
    return buffer

# ----------------------------------------------

serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(server_addr)
print ("The server is ready to receive")

f = open(filePath, 'wb')

while True:
    file_write()

    calculate_rwnd(LastByteRcvd, LastByteRead, RcvBuffer, rwnd)

    # print('[LastByteRead, LastByteRcvd] = [%d, %d]' % (LastByteRead, LastByteRcvd))

    data, client_addr = serverSocket.recvfrom(BUF_SIZE)

    # 客户端发送的第一个包为文件大小包，不用回复
    if num_of_times == -1:
        num_of_times = int(data)
        continue

    elif data == 'exit':
        serverSocket.sendto(pickle.dumps(s_pkt(rwnd, 'exit')), client_addr)
        done = 1
        continue
    
    elif data == '' and rwnd > 0:
        print('let\'s go!')
        serverSocket.sendto(pickle.dumps(s_pkt(rwnd, LastByteRead)), client_addr)
        continue
    
    elif rwnd > 0:
        client_pkt = pickle.loads(data)

        if LastByteRcvd == -1:
            LastByteRcvd = client_pkt.seq
            windows[client_pkt.seq] = client_pkt.data
            seqs[client_pkt.seq] = 1
            # file_write() # （尝试）读入文件
            serverSocket.sendto(pickle.dumps(s_pkt(rwnd, LastByteRead)), client_addr)
            continue

        up_limit = (LastByteRcvd + rwnd) % seq_limit
        down_limit = LastByteRead
        up_new = up_limit
        down_new = (LastByteRcvd + 1) % seq_limit

        # print('limit: [%d, %d]' % (down_limit, up_limit))
        # print('new: [%d, %d]' % (down_new, up_new))

        # 出界或收到过的包
        if ((up_limit > down_limit and (client_pkt.seq > up_limit or client_pkt.seq < down_limit)) or
            (up_limit < down_limit and (client_pkt.seq > up_limit and client_pkt.seq < down_limit)) or
            (client_pkt.seq in seqs and seqs[client_pkt.seq] == 1)
            ):
            # print(client_pkt.seq)
            serverSocket.sendto(pickle.dumps(s_pkt(rwnd, LastByteRead)), client_addr)
            continue

        # 窗口内且序号大于LastByteRcvd的包
        if ((up_new >= down_new and client_pkt.seq >= down_new and client_pkt.seq <= up_new) or
            (up_new < down_new and (client_pkt.seq >= down_new or client_pkt.seq <= up_new))):
            LastByteRcvd = client_pkt.seq
        
        windows[client_pkt.seq] = client_pkt.data
        seqs[client_pkt.seq] = 1
        serverSocket.sendto(pickle.dumps(s_pkt(rwnd, LastByteRead)), client_addr)
    
    else:
        serverSocket.sendto(pickle.dumps(s_pkt(rwnd, LastByteRead)), client_addr)


