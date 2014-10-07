```
     _/_/_/                    _/                                     
    _/    _/    _/_/      _/_/_/    _/_/      _/_/    _/_/_/  _/_/    
   _/_/_/    _/_/_/_/  _/    _/  _/_/_/_/  _/_/_/_/  _/    _/    _/   
  _/    _/  _/        _/    _/  _/        _/        _/    _/    _/    
 _/    _/    _/_/_/    _/_/_/    _/_/_/    _/_/_/  _/    _/    _/     
```

Redeem is the Replicape Daemon that accepts G-codes and turns them into coordinates on 
your 3D-printer. It's similar to Marlin and Teacup, only it's taylor made for Replicape and it's written in Python. 

Software features:  
- Accelleration with corner speed prediction.  
- Printer settings loaded from file  
- Controllable via ethernet, USB, printer display.   

Wiki: (http://wiki.thing-printer.com/index.php?title=Redeem)

Ipk packets (for Angstrom/Opkg) are available: 
  http://feeds.thing-printer.com/feeds/v2014.06/ipk/eglibc/armv7at2hf-vfp-neon/machine/beaglebone/

# Installation:  
You can clone this repository directly on your BBB:  
```
ssh root@192.168.7.2
cd /usr/src  
git clone https://intelligentagent@bitbucket.org/intelligentagent/redeem.git  
```
Make sure gcc, swig, python-dev, binutils and g++ is installed before compiling the native path planner.  
`opkg install swig python-dev gcc binutils g++`

For Debian, install swig, python-smbus:  
`apt-get install swig python-smbus`

Compile the native path planner module:  
```
cd /usr/src/redeem/software/path_planner  
python setup.py install  
chmod +x /usr/src/redeem/software/Redeem.py
```
Get and compile the device tree overlay. Notice that there has been a change in the dt interace between 3.8 and 3.12:  
```
wget https://bitbucket.org/intelligentagent/replicape/raw/7bd19bb1be34aa4c32953e8175177d130c6dca10/Device_tree/3.8/BB-BONE-REPLICAP-0A4A.dts
dtc -O dtb -o /lib/firmware/BB-BONE-REPLICAP-0A4A.dtbo -b 0 -@ BB-BONE-REPLICAP-0A4A.dts
```
Disable HDMI with sound (will load HDMI without sound):  
`nano /boot/uboot/uEnv.txt`  
Add this line:  
`optargs=capemgr.disable_partno=BB-BONELT-HDMI`
    
The capemgr does not work with Debian, so the cape has to be enabled manually:  
`nano /etc/default/capemgr`  
Add this line:  
`CAPE=BB-BONE-REPLICAP:0A4A`  
After a reboot, you should see a the cape firmware load:  
`dmesg | grep -i replic`  

Copy the config files: 
```
mkdir -p /etc/redeem
cp /usr/src/redeem/configs/*.cfg /etc/redeem/
```

For communicating with octoprint etc. Redeem uses a virtual tty:
```
cd /usr/src/  
git clone https://github.com/eliasbakken/tty0tty  
cd tty0tty/pts   
make  
make install  
```  
Enable the redeem service:  
```
cp /usr/src/redeem/systemd/redeem.service /lib/systemd/system/redeem.service  
systemctl enable redeem.service  
systemctl start redeem.service  
```
# Development:  
  Try to be PEP8 compliant: http://legacy.python.org/dev/peps/pep-0008/