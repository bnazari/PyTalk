#!/usr/bin/python

from time import time, sleep, clock, localtime, strftime
from random import randint
import socket
import struct
import thread
import shlex
import alsaaudio 
from numpy import linspace,sin,pi,int16
from serial import Serial

def note(freq, len, amp=1, rate=8000):
 t = linspace(0,len,len*rate)
 data = sin(2*pi*freq*t)*amp
 return data.astype(int16) 
idle_time = time()
ipAddress = "127.0.0.1"

silence = chr(0)* 32000

def rxAudioStream():
    global ipAddress
    print('Start audio thread')
    
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
        if (soundData[0:4] == 'USRP'):
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
#                print(eye, seq, memory, keyup, talkgroup, type, mpxid, reserved, len(audio), len(soundData))
                if (keyup != lastKey):
#                    print('key' if keyup else 'unkey')
                    if keyup:
#                       p.write(silence)
                      start_time = time()
                    if keyup == False:
#                       if (time() - start_time)>=1.2:
#                         tones();
                       print '{} {} {} {} {} {} {:.2f}s'.format(
                                                                    strftime("%m/%d/%y", localtime(start_time)),
                                                                    strftime("%H:%M:%S", localtime(start_time)),
                                                                    call, rxslot, tg, loss, time() - start_time)
                       idle_time = time()
                    lastKey = keyup
                if (len(audio) == 320):
                    if bt_up == False:
                        p = alsaaudio.PCM(type=alsaaudio.PCM_PLAYBACK)
                        p.setformat(alsaaudio.PCM_FORMAT_S16_LE)
                        p.setrate(8000)
                        p.setchannels(1)
                        p.setperiodsize(160)
                        bt_up = True
                        print('Attach BT')
                        idle_time = time()
                    p.write(audio)
            if (type == 2): #metadata
                audio = soundData[32:]
                if ord(audio[0]) == 8:
                    tg = (ord(audio[9]) << 16) + (ord(audio[10]) << 8) + ord(audio[11])
                    rxslot = ord(audio[12]);
                    call = audio[14:]
        else:
            print(soundData, len(soundData))
      except socket.timeout:
        if (bt_up==True):
           if (time() - idle_time >=5):
              print('Release BT')
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
                usrp = 'USRP' + struct.pack('>iiiiiii',seq, 0, ptt, 0, 0, 0, 0)
                udp.sendto(usrp, (ipAddress, 34001))
                seq = seq + 1
                print 'PTT: {}'.format(ptt)
                bt_tx=0
                q.close()
            lastPtt = ptt
            if ptt:
                if bt_tx==0:
                  q = alsaaudio.PCM(type=alsaaudio.PCM_CAPTURE)
                  q.setformat(alsaaudio.PCM_FORMAT_S16_LE)
                  q.setrate(8000)
                  q.setchannels(1)
                  q.setperiodsize(160)
                  bt_tx=1
                audio = q.read()
                usrp = 'USRP' + struct.pack('>iiiiiii',seq, 0, ptt, 0, 0, 0, 0) + audio[1]
                udp.sendto(usrp, (ipAddress, 34001))
                seq = seq + 1
        except:
            print("overflow")
ptt = False     # toggle this to transmit (left up to you)
ser = Serial('/dev/rfcomm0', 9600)

thread.start_new_thread( rxAudioStream, () )
thread.start_new_thread( txAudioStream, () )

ptt_button=''
while True:
    sleep(0.02)
    ptt_button = ser.read(6)
    if (ptt_button=='+PTT=P'):
      ptt=True
      ptt_button=''
    if (ptt_button=='+PTT=R'):
      ptt=False
      ptt_button=''
