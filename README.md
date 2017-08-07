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
- Controllable via OctoPrint, ethernet, USB, Manga Screen (Toggle on 4.3" LCD).   

[Redeem documentation on the wiki](http://wiki.thing-printer.com/index.php?title=Redeem)

# Installation:
## Complete Debian based eMMC flasher image  
Most users should probably use the [Kamikaze CNC image](http://wiki.thing-printer.com/index.php?title=Kamikaze), it is a complete BeagleBone eMMC flasher image that comes with Redeem. 

## Debain package
If you have a different Debian distro, you can use the .deb packages form the thing-printer feed:  
```
wget -O - http://kamikaze.thing-printer.com/apt/public.gpg | apt-key add -
echo "deb [arch=armhf] http://kamikaze.thing-printer.com/apt ./" >> /etc/apt/sources.list
apt-get update
apt-get install redeem
```

## Installation from source

### Requirements
These instructions assumes you have a kernel with a cape manager, meaning kernel > 4.

### Installation
You can clone this repository directly on your BBB:  
```
ssh root@192.168.7.2
cd /usr/src  
git clone https://intelligentagent@bitbucket.org/intelligentagent/redeem.git  
```

For Debian, install swig, python-smbus:  
`apt-get install swig python-smbus`

Compile the native path planner module:  
```
cd /usr/src/redeem/
python setup.py install  
mkdir /etc/redeem
cp configs/* /etc/redeem
cp data/* /etc/redeem
```



### Device tree overlay
Get and compile the device tree overlay.  
For Kernel 4.1, see the instructions for the new [cape overlay repository](https://github.com/beagleboard/bb.org-overlays)  
 
Disable HDMI with sound (will load HDMI without sound):  

For post uboot v2014.07/v2014.10/v2015.01 images
`nano /boot/uEnv.txt`  

Change this line:  
`#cape_disable=capemgr.disable_partno=BB-BONELT-HDMI`
to
`cape_disable=capemgr.disable_partno=BB-BONELT-HDMI`

Reboot

After a reboot, you should see a the cape firmware load:  
`dmesg | grep -i replic`  

Enable the redeem service:  


### Change startup script location

If you have the Debian package based version installed along side, 
you have to change the startup script from /usr/bin to /usr/local/bin:
```
nano /lib/systemd/system/redeem.service
systemctl daemon-reload
systemctl restart redeem
```

If you do not have the file "/lib/systemd/system/redeem.service" instlled: 
First modify the redeem.service file to update redeem 'binary' location.
Since the software was sintalled form source, it is added to /usr/local
`nano /usr/src/redeem/systemd/redeem.service`

Edit line
`ExecStart=/usr/bin/redeem`
to
`ExecStart=/usr/local/bin/redeem`

Copy redeem systemd startup script into place, enable it for startup on boot and start it now.

```
cp /usr/src/redeem/systemd/redeem.service /lib/systemd/system/redeem.service  
systemctl enable redeem.service  
systemctl start redeem.service  
```


# Development:  
  Try to be PEP8 compliant: http://legacy.python.org/dev/peps/pep-0008/

## Locating files 
Do an "updatedb" and then "locate Redeem.py". It should give you the location. Please note that
if you install from source, the files will have a different location than if you install from a deb package.
/usr/lib vs. /usr/local/lib/.

## Making firmware changes
As for the firmware files (the code that runs on PRUSS), they are moved to /tmp during compilation, but should reside in a sub directory from Redeem.py before compilation.
A recompile of the firmware can be triggered by touching /et/redeem/local.cfg

# Contributors
Elias Bakken
Mathieu Monney
Daryl Bond
Andrew Wiley






# Install Redeem on Debian 8.3 (WIP)
 - Disable universal cape manager
    nano /boot/uEnv.txt
    delete cape_universal=enable
 - Download and install Replicape firmware
    git clone https://github.com/eliasbakken/bb.org-overlays
    cd bb.org-overlays/
    ./dtc-overlay.sh
    ./install.sh
 - Manual installation of redeem from feed
 - Disable logging to file
    nano /etc/redeem/local.cfg
 - Disable loading overlays
   nano /opt/source/adafruit-beaglebone-io-python/source/spimodule.c
 - Install socat
 - Install octoprint
 - Install python-octoprint-redeem

