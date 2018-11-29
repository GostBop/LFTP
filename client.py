# -*- coding=utf-8 -*-
from __future__ import print_function
from socket import *
import pickle, random, threading, time, os, sys, Queue

# -----------------------------------------------
''' classes
'''

class c_pkt(object):
  # client packet which has base(seq number) and data
  def __init__(self, base, data):
      self.base = base 
      self.data = data

class s_pkt(object):
  # server packet which has ack and rwnd
  def __init__(self, ack, rwnd):
      self.ack = ack
      self.rwnd = rwnd

# -----------------------------------------------
''' globals
'''

windows = Queue.Queue()

server_addr = ('192.168.43.181', 31500)


seq_limit = 1000
time_limit = 1.5
time_count = 0
data_size = 20000
packet_size = 60000

filePath = "D:\maogai.zip"
file_size = os.path.getsize(filePath)
num_of_times = file_size / data_size

base = 0 # (LstByteAcked + 1) % seq_limit
nextseq = 0 # (LastByteSent + 1) % seq_limit
rwnd = 20

count = 0
start = 0

lock = threading.Lock()

# -----------------------------------------------
''' functions
'''

def progress(percent , width = 50):
	if percent >= 100:
		percent = 100
	show_str = ('[%%-%ds]' % width) % (int(width * percent / 100) * "#")
	print('\r%s %d%%' % (show_str, percent), end = '')

def resend():
  '''
    send all the packet in the windows, 
    which have been sent but not acked yet
  '''
  
  global timer, lock, time_count
  lock.acquire()
  win_size = windows.qsize()
  for _ in range(0, win_size):
    packet = windows.get()
    client_socket.sendto(packet, server_addr)
    p = pickle.loads(packet)
    print("resend %d" % int(p.base))
    
    windows.put(packet)
  lock.release()
  print("time_count %d" % time_count)
  time_count = time_count + 1
  timer = threading.Timer(time_limit + time_count, resend)
  timer.start()

def receive():
  '''
    receive from server, and if there is no response,
    resend all the packet
  '''
  global base, timer, rwnd, count, start, lock, time_count
  while True:
    if start == 0:
      continue
    if rwnd != 0:
      timer = threading.Timer(time_limit, resend)
      timer.start()
    # if rwnd is 0, the transmit function will send(resend) packet
    response, _ = client_socket.recvfrom(packet_size)
    if response == "exit":
      print(" server exit") 
      timer.cancel()
      break
    else:

      server_pkt = pickle.loads(response)
      print ("ack: %d" % int(server_pkt.ack))
      if int(server_pkt.ack) == base or int(server_pkt.ack) >= ((base + 1) % seq_limit):
        base = (int(server_pkt.ack) + 1) % seq_limit
        print ("base: %d" % base)
        rwnd = int(server_pkt.rwnd)
        timer.cancel()
        time_count = 0
        lock.acquire()
        while not windows.empty():
          count = count + 1
      
          packet = windows.get()
          p = pickle.loads(packet)
          print ("pop: %d" % int(p.base))
          if ((p.base + 1) % seq_limit) >= base:
            break
        lock.release()
        progress(100 * count / num_of_times)

def send_a_packet():
  global f, data_size, nextseq, server_addr
  data = f.read(data_size)
  if data:
    packet = pickle.dumps(c_pkt(nextseq, data))
    client_socket.sendto(packet, server_addr)
    windows.put(packet)
    nextseq = (nextseq + 1) % seq_limit
  else:
    client_socket.sendto("exit " + str(nextseq), server_addr)

def transmit():
  '''
    send new packet when there are still spaces,
    and send a small packet when rwnd is 0
  '''
  global start, nextseq, base, seq_limit, rwnd, f, data_size, windows, lock
  while True:
    # number of packets sent but not acked should smaller than rwnd
    if (nextseq - base + seq_limit) % seq_limit < rwnd:
      data = f.read(data_size)
      if data:
        packet = pickle.dumps(c_pkt(nextseq, data))
        client_socket.sendto(packet, server_addr)
        start = 1
        lock.acquire()
        windows.put(packet)
        lock.release()
        #print("put: %d" % nextseq)
        nextseq = (nextseq + 1) % seq_limit
      else:
        print(" send exit", end = '') 
        client_socket.sendto("exit " + str(nextseq), server_addr)
        windows.put(packet) # ?
        break
    # do sth when rwnd is 0
    elif rwnd == 0:
      client_socket.sendto("", server_addr)

# -----------------------------------------------

client_socket = socket(AF_INET, SOCK_DGRAM)
f = open(filePath.decode('UTF-8'), 'rb')
# global timer
timer = threading.Timer(time_limit, resend)
# receive from server
t = threading.Thread(target = receive)
t.start()
# send packets
transmit()

t.join()
f.close()
client_socket.close()