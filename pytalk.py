#!/usr/bin/python

from time import time, sleep, clock, localtime, strftime
from random import randint
import socket
import struct
import _thread
import shlex
import alsaaudio 
from numpy import linspace,sin,pi,int16
from serial import Serial
import logging
from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s,%(levelname)s,%(message)s')

fh = logging.FileHandler('pytalk.log')
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)




clients = []
def send_websocket(message):
        for client in clients:
            client.sendMessage(u'DATA,'+message)

class PyTalkClient(WebSocket):
   def handleMessage(self):
      for client in clients:
         if client != self:
            client.sendMessage(u'MESSAGE,' + self.address[0] + u',' + self.data)

   def handleConnected(self):
      logger.info('Websocket,{},connected'.format(self.address))
      for client in clients:
         client.sendMessage(u'MESSAGE,' + self.address[0] + u',connected')
      clients.append(self)

   def handleClose(self):
      clients.remove(self)
      logger.info('Websocket,{},close'.format(self.address))
      for client in clients:
         client.sendMessage(u'MESSAGE,' +self.address[0] + u',disconnected')

server = SimpleWebSocketServer('', 8000,PyTalkClient)
_thread.start_new_thread( server.serveforever, () )

def note(freq, len, amp=1, rate=8000):
 t = linspace(0,len,len*rate)
 data = sin(2*pi*freq*t)*amp
 return data.astype(int16) 
idle_time = time()
ipAddress = "127.0.0.1"

silence = chr(0)* 32000

def rxAudioStream():
    global ipAddress
    logger.info('Start DMR')

    def tones():
       p.write(note(900, .2, amp=1000, rate=8000))
       p.write(note(600, .2, amp=1000, rate=8000))
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    udp.bind(("", 32001))
    udp.settimeout(.2)
    bt_up = False
    lastKey = -1
    start_time = time()
    call = ''
    tg = ''
    loss = '0.00%'
    rxslot = '0'
    while True:
       
      try:
        soundData, addr = udp.recvfrom(1024)
        if addr[0] != ipAddress:
            ipAddress = addr[0]
        if (soundData[0:4].decode('utf-8') == 'USRP'):
            eye = soundData[0:4]
            seq, = struct.unpack(">i", soundData[4:8])
            memory, = struct.unpack(">i", soundData[8:12])
            keyup, = struct.unpack(">i", soundData[12:16])
            talkgroup, = struct.unpack(">i", soundData[16:20])
            type, = struct.unpack("i", soundData[20:24])
            mpxid, = struct.unpack(">i", soundData[24:28])
            reserved, = struct.unpack(">i", soundData[28:32])
            audio = soundData[32:]
            if (type == 0): # voice
                audio = soundData[32:]
                logger.debug('%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,',eye, seq, memory, keyup, talkgroup, type, mpxid, reserved, len(audio), len(soundData))
                if (keyup != lastKey):
                    if keyup:
                       if bt_up == False:					
                         p = alsaaudio.PCM(type=alsaaudio.PCM_PLAYBACK)
                         p.setformat(alsaaudio.PCM_FORMAT_S16_LE)
                         p.setrate(8000)
                         p.setchannels(1)
                         p.setperiodsize(160)
                         bt_up = True
                         logger.info('Attach_BT')
                         send_websocket('Attach_BT')
                       p.write(silence)
                       start_time = time()
                       message='RX_Start,{0},{1},0.0'.format(call, tg)
                       logger.info(message)
                       send_websocket(message)
                    if keyup == False:
#                      if (time() - start_time)>=1.2:
#                         tones();
                       message='RX_Stop,{0},{1},{2:.2f}'.format(call,tg,(time() - start_time))
                       logger.info(message)
                       send_websocket(message)                      
                    lastKey = keyup
                if (len(audio) == 320):
                    p.write(audio)
                idle_time = time()
            if (type == 2): #metadata
                audio = soundData[32:]
                if audio[0] == 8:
                    tg = (audio[9] << 16) + (audio[10] << 8) + audio[11]
                    rxslot = audio[12];
                    call = audio[14:].decode('utf-8')
        else:
            print((soundData, len(soundData)))
      except socket.timeout:
        if (bt_up==True):
           if (time() - idle_time >=5):
              logger.info('Detach_BT')
              send_websocket('Detach_BT')
              p.close()
              bt_up=False
        continue
    udp.close()

def txAudioStream():
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    lastPtt = ptt
    seq = 0
    bt_tx=0
    while True:
        try: 
            if ptt != lastPtt:
                usrp = 'USRP'.encode() + struct.pack('>iiiiiii',seq, 0, ptt, 0, 0, 0, 0)
                udp.sendto(usrp, (ipAddress, 34001))
                seq = seq + 1
                message='PTT,{}'.format(ptt)
                logger.info(message)
                send_websocket(message)
                if ptt==True:
                  q = alsaaudio.PCM(type=alsaaudio.PCM_CAPTURE)
                  q.setformat(alsaaudio.PCM_FORMAT_S16_LE)
                  q.setrate(8000)
                  q.setchannels(1)
                  q.setperiodsize(160)
                  bt_tx=1
                if ptt==False:
                   q.close()
            lastPtt = ptt
            if ptt:
                audio = q.read()
                usrp = 'USRP'.encode() + struct.pack('>iiiiiii',seq, 0, ptt, 0, 0, 0, 0) + audio[1]
                udp.sendto(usrp, (ipAddress, 34001))
                seq = seq + 1
        except:
            logger.warning('Overflow')
        sleep(0.02)

ptt = False     # toggle this to transmit (left up to you)
ser = Serial('/dev/rfcomm0', 9600)

_thread.start_new_thread( rxAudioStream, () )
_thread.start_new_thread( txAudioStream, () )
ptt_button=''
while True:
    sleep(0.02)
    ptt_button = ser.read(6).decode('utf-8')
    if (ptt_button=='+PTT=P'):
      ptt=True
      ptt_button=''
    if (ptt_button=='+PTT=R'):
      sleep(.3)
      ptt=False
      ptt_button=''
