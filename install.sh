wget http://dvswitch.org/install-allstarlink-repository
chmod +x install-allstarlink-repository
sudo ./install-allstarlink-repository
sudo apt-get -y update
sudo apt-get -y upgrade
sudo apt-get  -y install raspberrypi-kernel-headers dvswitch python-gpiozero python-numpy libasound2-dev python-dev
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
sudo python get-pip.py
sudo pip install pyalsaaudio

chmod +x tune.sh
chmod +x vol.sh

sudo cp pytalk.service /etc/systemd/system/pytalk.service
sudo cp MMDVM_Bridge.ini /opt/MMDVM_Bridge/MMDVM_Bridge.ini
sudo cp Analog_Bridge.ini /opt/Analog_Bridge/Analog_Bridge.ini
sudo wget -O mic mic.raspiaudio.com
sudo wget -O test test.raspiaudio.com

sudo systemctl enable mmdvm_bridge.service 
sudo systemctl enable analog_bridge.service
sudo systemctl enable md380-emu.service
sudo systemctl enable pytalk

sudo bash mic
