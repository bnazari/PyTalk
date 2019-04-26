# PyTalk

Project turns you raspberry Pi into standalone network radio. 

Following hardware have been used: **RASPIAUDIO.COM Audio DAC HAT Sound Card (AUDIO+SPEAKER+MIC)**

PyTalk service relies on /home/pi/PyTalk directory so consider running command below under **pi** user from home directory

Installation:
  - git clone https://github.com/bnazari/PyTalk.git
  - cd PyTalk
  - update **MMDVM_Bridge.ini** with your callsing, DMR ID and password (if you have **Hotspot Security** enabled)
  - in **Analog_Bridge.ini** update **gatewayDmrId** and **repeaterID** with your DMR ID and repeater/hotspot DMR ID, change **txTg** to destination talkgroup number (i.e. 31000 for Brandmeister parrot)
  - chmod +x install.sh
  - ./install.sh

There will be automated check of speakers and microphone at the very end of installation process.

After installation is done DMR static talk groups can be managed in "**Brandmeister**" - "**My hotspots**" console
