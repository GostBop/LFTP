# coding:utf-8
import socket
import os
import pickle
import threading
import Queue
import time
import gc
import binascii 

class UDP(object):
    def __init__(self, base, file):
        self.base = base 
        self.file = file

class ACK(object):
    def __init__(self, ack, rwnd):
        self.ack = ack
        self.rwnd = rwnd

base = 0
nextseq = 0
windows = Queue.Queue()
count = 0
rwnd = 20

address = ('127.0.0.1', 31500)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
file = open("C:\Users\Sandman\Desktop\\test.mp4".decode('UTF-8'), 'rb')

buffer = file.read(1024)
if not buffer:
  s.sendto("exit", address)
udp = UDP(nextseq, buffer)
data = pickle.dumps(udp)
s.sendto(data, address)
windows.put(data)
nextseq = nextseq + 1

def chongchuan():
  print "chongchuan"
  lock = threading.Lock()
  lock.acquire()
  n = windows.qsize()
  for _ in range(0, n):
    data = windows.get()
    s.sendto(data, address)
    windows.put(data)
  lock.release()
  timer = threading.Timer(1.0, chongchuan)
  timer.start()

def jieshou():
  while True:
    timer = threading.Timer(1.0, chongchuan)
    timer.start()
    global base
    response, _ = s.recvfrom(6000)
    if response == "exit":
      print "b"
      timer.cancel()
      break
    res = pickle.loads(response)

    base = int(res.ack) + 1
    rwnd = int(res.rwnd)
    if base == 1000:
      base = 0
    timer.cancel()

t = threading.Thread(target=jieshou)
t.start()
while True:
  if (nextseq + 1000 - base) % 1000 < rwnd:
    buffer = file.read(1024)
    if not buffer:
      s.sendto("exit" + str(nextseq), address)
      print "a"
      windows.put(data)
      break
    data = pickle.dumps(UDP(nextseq, buffer))
    nextseq = nextseq + 1
    if nextseq == 1000:
      nextseq = 0
    windows.put(data)
    s.sendto(data, address)
t.join()
file.close()
s.close()