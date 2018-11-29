# coding:utf-8
import socket
import os
import pickle
import Queue
import threading
import time
class UDP(object):
    def __init__(self, base, file):
        self.base = base 
        self.file = file

class ACK(object):
    def __init__(self, ack, rwnd):
        self.ack = ack
        self.rwnd = rwnd

loc = ('', 31500)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(loc)
#ss = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

ack = -1
LastRecv = 0
LastRead = 0
RcvBuffer = 20
rwnd = RcvBuffer
windows = Queue.Queue()

file = open("C:\Users\Sandman\Desktop\\test_copy2.mp4".decode('utf-8'), 'ab')

def write():
  global LastRead
  while True:
    #time.sleep(0.5)
    while not windows.empty():
      file.write(windows.get())
      LastRead = (LastRead + 1) % 1000

t = threading.Thread(target=write)
t.start()

while True:
  data, addr = s.recvfrom(6000)
  a = (ack + 1) % 1000
  if data == "exit" + str(a):
    s.sendto("exit", addr)
    print data
    #time.sleep(5)
    break
  buffer = pickle.loads(data)
  #print LastRead, " ", LastRecv
  if buffer.base == (ack + 1) % 1000 and (LastRecv - LastRead + 1000) % 1000 <= RcvBuffer:
    #file.write((buffer.file))
    LastRecv = (LastRecv + 1) % 1000
    windows.put(buffer.file)
    rwnd = RcvBuffer - (LastRecv - LastRead + 1000) % 1000
    response = pickle.dumps(ACK(buffer.base, rwnd))
    s.sendto(response, addr)
    ack = buffer.base

print "c"
file.close()
s.close()
print "d"