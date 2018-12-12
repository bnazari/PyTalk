#!/usr/bin/python
###################################################################################
# Copyright (C) 2014, 2015, 2016, 2017, 2018 N4IRR
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND ISC DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS.  IN NO EVENT SHALL ISC BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE
# OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.
###################################################################################

from time import time, sleep, clock, localtime, strftime
from random import randint
import socket
import struct
import thread
import shlex
import pyaudio
from gpiozero import LED, Button
from numpy import linspace,sin,pi,int16

def note(freq, len, amp=1, rate=8000):
 t = linspace(0,len,len*rate)
 data = sin(2*pi*freq*t)*amp
 return data.astype(int16) 

ipAddress = "127.0.0.1"
led = LED(25)
button = Button(23)


silence = chr(0)* 2048


def rxAudioStream():
    global ipAddress
    print('Start audio thread')
    
    FORMAT = pyaudio.paInt16
    CHUNK =1024 
    CHANNELS = 1
    RATE = 8000
    
    stream = p.open(format=FORMAT,
                    channels = CHANNELS,
                    rate = RATE,
                    output = True,
                    frames_per_buffer = CHUNK,
                    )
    def play(data):
     if data == '':
        data = silence
     stream.write(audio,160)
    
    def tones():
       stream.write(note(900, .2, amp=1000, rate=RATE))
       stream.write(note(600, .2, amp=1000, rate=RATE))
    
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    udp.bind(("", 32001))
    
    lastKey = -1
    start_time = time()
    call = ''
    tg = ''
    loss = '0.00%'
    rxslot = '0'
    while True:
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
                #print(eye, seq, memory, keyup, talkgroup, type, mpxid, reserved, audio, len(audio), len(soundData))
                if (len(audio) == 320):
                    # stream.write(audio,160)
                    play(audio)
                if (keyup != lastKey):
#                    print('key' if keyup else 'unkey')
                    if keyup:
                        start_time = time()
                    if keyup == False:
                        tones(); 
                        print '{} {} {} {} {} {} {:.2f}s'.format(
                                                                    strftime(" %m/%d/%y", localtime(start_time)),
                                                                    strftime("%H:%M:%S", localtime(start_time)),
                                                                    call, rxslot, tg, loss, time() - start_time)
                    lastKey = keyup
            if (type == 2): #metadata
                audio = soundData[32:]
                if ord(audio[0]) == 8:
                    tg = (ord(audio[9]) << 16) + (ord(audio[10]) << 8) + ord(audio[11])
                    rxslot = ord(audio[12]);
                    call = audio[14:]

        else:
            print(soundData, len(soundData))

    udp.close()

def txAudioStream():
    FORMAT = pyaudio.paInt16
    CHUNK = 160
    CHANNELS = 1
    RATE = 8000
    
    stream = p.open(format=FORMAT,
                    channels = CHANNELS,
                    rate = RATE,
                    input = True,
                    frames_per_buffer = CHUNK,
                    )
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    lastPtt = ptt
    seq = 0
    while True:
        try:
            audio = stream.read(160, exception_on_overflow=False)
            if ptt != lastPtt:
                usrp = 'USRP' + struct.pack('>iiiiiii',seq, 0, ptt, 0, 0, 0, 0)
                udp.sendto(usrp, (ipAddress, 34001))
                seq = seq + 1
                print 'PTT: {}'.format(ptt)
            lastPtt = ptt
            if ptt:
                usrp = 'USRP' + struct.pack('>iiiiiii',seq, 0, ptt, 0, 0, 0, 0) + audio
                udp.sendto(usrp, (ipAddress, 34001))
                print 'transmitting'
                seq = seq + 1
        except:
            print("overflow")

ptt = False     # toggle this to transmit (left up to you)

p = pyaudio.PyAudio()
thread.start_new_thread( rxAudioStream, () )
thread.start_new_thread( txAudioStream, () )

while True:
    if button.is_pressed:
        led.on()
        ptt=True
    else:
        led.off()
        ptt=False
    sleep(0.02)
