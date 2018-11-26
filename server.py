# coding:UTF-8
import socket
import os
import json
import binascii 
class UDP(object):
    def __init__(self, base, file):
        self.base = base 
        self.file = file

def dict2UDP(d):
    return UDP(d['base'], d['file'])

loc = ('', 31500)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(loc)
#ss = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

ack = -1

file = open("D:/maogai.zip".decode('utf-8'), 'ab')

while True:
  data, addr = s.recvfrom(6000)
  a = (ack + 1) % 1000
  if data == "exit" + str(a):
    s.sendto("exit", addr)
    break
  buffer = json.loads(data, object_hook=dict2UDP)
  if buffer.base == (ack + 1) % 1000:
    file.write(binascii.a2b_hex(buffer.file))
    s.sendto(str(buffer.base), addr)
    ack = buffer.base

file.close()
s.close()