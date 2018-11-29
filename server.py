# coding:utf-8
import socket, os, pickle, Queue, threading, time

# -----------------------------------------------
''' things to do...

  1.let the client tell server its file size(to show the progress)
  2.add print function to show the rate of progress
  3.do sth when rwnd is 0
  4.determine the time to close the file and socket
  5.why should the client send a packet at the beginning ?

'''

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
server_addr = ('', 31500)

seq_limit = 1000
packet_size = 60000
RcvBuffer = 20

num_of_times = -1

ack = -1
LastByteRead = 0
LastByteRecv = 0 # (ack + 1) % seq_limit
rwnd = RcvBuffer
windows = Queue.Queue()

done = 0

# -----------------------------------------------
''' functions
'''

def write():
  global LastByteRead
  while True:
    time.sleep(1)
    if not windows.empty():
      f.write(windows.get())
      LastByteRead = (LastByteRead + 1) % seq_limit
    elif done == 1:
      break

# -----------------------------------------------

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(server_addr)
print "the server is ready to receive"

f = open("C:\Users\Sandman\Desktop\\test_copy.zip".decode('utf-8'), 'wb')

t = threading.Thread(target = write)
t.start()

while True:
  # print("wait to recv...")
  request, client_addr = server_socket.recvfrom(packet_size)
  # ensure all the packet is successly received
  if type(request) == str and request[0] == "e": # bug
    if request == "exit " + str((ack + 1) % seq_limit):
      # print("the client want to exit")
      server_socket.sendto("exit", client_addr)
      done = 1
      break
    continue
  
  rwnd = RcvBuffer - (LastByteRecv - LastByteRead + seq_limit) % seq_limit
  if rwnd == 0 or request == "":
    # print "rwnd = 0"
    server_socket.sendto(pickle.dumps(s_pkt(ack, rwnd)), client_addr)
  else:
    client_pkt = pickle.loads(request)
    # the seq is in order and there are still spaces left
    if (client_pkt.base == (ack + 1) % seq_limit and 
        (LastByteRecv - LastByteRead + seq_limit) % seq_limit <= RcvBuffer):
      # print("ack                              %d" % client_pkt.base)
      ack = client_pkt.base
      windows.put(client_pkt.data)
      LastByteRecv = (LastByteRecv + 1) % seq_limit
      rwnd = RcvBuffer - (LastByteRecv - LastByteRead + seq_limit) % seq_limit
      server_socket.sendto(pickle.dumps(s_pkt(client_pkt.base, rwnd)), client_addr)

f.close()
server_socket.close()
print "closed"