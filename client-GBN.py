# coding:utf-8
import socket
import os
import json
import threading
import Queue
import time
import gc
import binascii 

class UDP(object):
    def __init__(self, base, file):
        self.base = base 
        self.file = file

def udp2dict(udp):
    return {
        "base": udp.base,
        "file": udp.file
    }

base = 0
nextseq = 0
windows = Queue.Queue()
count = 0

address = ('127.0.0.1', 31500)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
file = open("D:/东西/资料/学术大礼�?-毛概.zip".decode('UTF-8'), 'rb')

buffer = file.read(1024)
if not buffer:
  s.sendto("exit", address)
udp = UDP(nextseq, binascii.b2a_hex(buffer))
data = json.dumps(udp, default=udp2dict)
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
    ack, _ = s.recvfrom(6000)
    if ack == "exit":
      break
    base = int(ack) + 1
    if base == 1000:
      base = 0
    timer.cancel()

t = threading.Thread(target=jieshou)
t.start()
while True:
  if (nextseq + 1000 - base) % 1000 < 100:
    buffer = file.read(1024)
    if not buffer:
      s.sendto("exit" + str(nextseq), address)
      windows.put(data)
      break
    data = json.dumps(UDP(nextseq, binascii.b2a_hex(buffer)), default=udp2dict)
    nextseq = nextseq + 1
    if nextseq == 1000:
      nextseq = 0
    windows.put(data)
    s.sendto(data, address)
t.join()
file.close()
s.close()