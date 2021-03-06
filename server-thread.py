# coding:utf-8
from __future__ import print_function
import socket, os, pickle, Queue, threading, time

# -----------------------------------------------
''' things to do...

  ¡Ì 1.let the client tell server its file size(to show the progress)
  ¡Ì 2.add print function to show the rate of progress
  ¡Ì 3.do sth when rwnd is 0
  4.determine the time to close the file and socket
  ¡Ì 5.why should the client send a packet at the beginning ?

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

class file_info(object):
  # the name and size of the file sent
  def __init__(self, name, size):
    self.name = name
    self.size = size

# -----------------------------------------------
''' globals
'''

seq_limit = 1000
packet_size = 60000
RcvBuffer = 100


port = 11111

'''ack = -1
LastByteRead = 0
LastByteRecv = 0 # (ack + 1) % seq_limit
rwnd = RcvBuffer
windows = Queue.Queue()

done = 0'''

# -----------------------------------------------
''' functions
'''

def write(p, LastByteRead, windows, done, f, server_socket):
  while True:
    #time.sleep(1)
    while not windows.empty():
      # print("write %d to file ~~~" % LastByteRead)
      f.write(windows.get())
      LastByteRead[0] = (LastByteRead[0] + 1) % seq_limit
      #print ("write: %d" % LastByteRead[0])
    if windows.empty() and done[0] == 1:
      print("[%d] empty and done" % p)
      time.sleep(5)
      f.close()
      server_socket.close()
      print("[%d] closed" % p)
      end_time = time.asctime( time.localtime(time.time()) )
      print("[%d] " % p, end = '')
      print("end time: ", end_time)
      break

# -----------------------------------------------
def server(p, filePath):
  server_addr = ('', p)
  ack = -1
  LastByteRead = [0]
  LastByteRecv = 0 # (ack + 1) % seq_limit
  rwnd = RcvBuffer
  windows = Queue.Queue()

  done = [0]

  server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  server_socket.bind(server_addr)
  print("[%d] the server is ready to receive" % p)
  

  f = open(filePath.decode('utf-8'), 'wb')

  t = threading.Thread(target = write, args=(p, LastByteRead, windows, done, f, server_socket))
  t.start()

  while True:
    # print("wait to recv...")
    request, client_addr = server_socket.recvfrom(packet_size)
    # ensure all the packet is successly received

    rwnd = RcvBuffer - (LastByteRecv - LastByteRead[0] + seq_limit) % seq_limit
    if rwnd == 0 or request == "No Buffer":
      # print("rwnd = %d    ack: %d" % (rwnd, ack))
      server_socket.sendto(pickle.dumps(s_pkt(ack, rwnd)), client_addr)
      continue

    elif request[0] == 'e':
      if request == "exit " + str((ack + 1) % seq_limit):
        # print("the client want to exit")
        server_socket.sendto("exit", client_addr)
        done[0] = 1
        break
      else:
        continue
    
    else:
      client_pkt = pickle.loads(request)
      #print ("re: %d" % LastByteRead[0])
      # the seq is in order and there are still spaces left
      if (client_pkt.base == (ack + 1) % seq_limit and 
          (LastByteRecv - LastByteRead[0] + seq_limit) % seq_limit <= RcvBuffer):
        # print("ack                              %d" % client_pkt.base)
        ack = client_pkt.base
        windows.put(client_pkt.data)
        LastByteRecv = (LastByteRecv + 1) % seq_limit
        rwnd = RcvBuffer - (LastByteRecv - LastByteRead[0] + seq_limit) % seq_limit
        server_socket.sendto(pickle.dumps(s_pkt(client_pkt.base, rwnd)), client_addr)
      else:
        # print("%d is too fast, I send ack: %d, rwnd: %d " % (client_pkt.base, ack, rwnd))
        server_socket.sendto(pickle.dumps(s_pkt(ack, rwnd)), client_addr)

if __name__ == '__main__':
  tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  
  # 监听端口:
  tcp.bind(('127.0.0.1', 9999))

  tcp.listen(3)
  print('Waiting for connection...')

  while True:
    # 接受一个新连接:
    sock, addr = tcp.accept()
    port = port + 1000
    sock.send(str(port))
    data = sock.recv(1024)
    file_recv = pickle.loads(data)
    sock.close()
    start_time = time.asctime( time.localtime(time.time()) )
    print("[%d] The uploaded port is: %d" % (port, port))
    print("[%d] The fileName is: %s" % (port, file_recv.name))
    file_size_Mb = file_recv.size / 1024.0 / 1024
    print("[%d] The fileSize is: %.1fMb" % (port, file_size_Mb))
    print("[%d] " % port, end = '')
    print("start time: ", start_time)
    filePath = 'C:\\Users\\Sandman\\Desktop\\test\\' + file_recv.name
    t = threading.Thread(target = server, args = (port, filePath))
    t.start()
