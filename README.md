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
- Controllable via ethernet, USB, Manga Screen (Toggle on 4.3" LCD).   

[Redeem documentation on the wiki](http://wiki.thing-printer.com/index.php?title=Redeem)

# Installation:  
Most users should probably use the [Kamikaze CNC image](http://wiki.thing-printer.com/index.php?title=Kamikaze), it is a complete BeagleBone eMMC flasher image that comes with Redeem. 

If you have a different Debian distro, you can use the .deb packages form the thing-printer feed:  
```
wget -O - http://feeds.thing-printer.com/apt/debian/conf/replicape.gpg.key | apt-key add -
echo "deb http://feeds.thing-printer.com/apt/debian jessie main" >> /etc/apt/sources.list
apt-get update
apt-get install redeem
```

## Installation from source
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

Get and compile the device tree overlay.  
For Kernel 4.1, see the instructions for the new [cape overlay repository](https://github.com/beagleboard/bb.org-overlays)  
 
Get and compile the device tree overlay. Notice that there has been a change in the DT intefrace between 3.8 and 3.12:  
For Kernel 3.8:
```
wget https://bitbucket.org/intelligentagent/replicape/raw/7bd19bb1be34aa4c32953e8175177d130c6dca10/Device_tree/3.8/BB-BONE-REPLICAP-0A4A.dts
dtc -O dtb -o /lib/firmware/BB-BONE-REPLICAP-0A4A.dtbo -b 0 -@ BB-BONE-REPLICAP-0A4A.dts
```
For kernel 3.12 +:  
```
wget https://bitbucket.org/intelligentagent/replicape/raw/7bd19bb1be34aa4c32953e8175177d130c6dca10/Device_tree/3.12/BB-BONE-REPLICAP-0A4A.dts
dtc -O dtb -o /lib/firmware/BB-BONE-REPLICAP-0A4A.dtbo -b 0 -@ BB-BONE-REPLICAP-0A4A.dts
```

Disable HDMI with sound (will load HDMI without sound):  

For pre uboot v2014.07/v2014.10/v2015.01 images

`nano /boot/uboot/uEnv.txt`  
Add this line:  
`optargs=capemgr.disable_partno=BB-BONELT-HDMI`

For post uboot v2014.07/v2014.10/v2015.01 images

`nano /boot/uEnv.txt`  

Change this line:  
`#cape_disable=capemgr.disable_partno=BB-BONELT-HDMI`
to
`cape_disable=capemgr.disable_partno=BB-BONELT-HDMI`

The capemgr does not work with Debian, so the cape has to be enabled manually:  
`nano /etc/default/capemgr`  
Add this line:  
`CAPE=BB-BONE-REPLICAP:0A4A`  

Enable Adafruit SPI0 overlay on boot - needed for at least March 1st 2015 Debian image for BBB, possibly for everything post uboot v2014.07/v2014.10/v2015.1 images.

`nano /boot/uEnv.txt`  

Add this line:  
`cape_enable=capemgr.enable_partno=ADAFRUIT-SPI0`

Also need to rebuild the initrd image so it includes the Adafruit SPI0 overlay, this will insert all overylays in /lib/firmware. Useful if you need to add future overlays for boot time application. Copied and updated from https://github.com/notro/fbtft/wiki/BeagleBone-Black

Create /etc/initramfs-tools/hooks/dtbo

```
#!/bin/sh

set -e

. /usr/share/initramfs-tools/hook-functions

# Copy Device Tree fragments
mkdir -p "${DESTDIR}/lib/firmware"
cp -p /lib/firmware/*.dtbo "${DESTDIR}/lib/firmware/"
```

Make executable

`$ sudo chmod +x /etc/initramfs-tools/hooks/dtbo`
Backup initrd:

`$ sudo cp /boot/initrd.img-\`uname - r\` /boot/uboot/initrd.img-\`uname -r\`.bak`

Create/update initramfs:

`$ sudo /usr/sbin/update-initramfs`

Reboot

After a reboot, you should see a the cape firmware load:  
`dmesg | grep -i replic`  

Enable the redeem service:  

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

## Angstrom
For Angstrom the packages are outdated, install from source. For legacy packages, look here: 
[http://feeds.thing-printer.com/feeds/v2013.06/ipk/eglibc/armv7ahf-vfp-neon/machine/beaglebone/]

# Development:  
  Try to be PEP8 compliant: http://legacy.python.org/dev/peps/pep-0008/

# Locating files 
Hi! do an "updatedb" and then "locate Redeem.py". It should give you the location. Please note that
if you install from source, the files will have a different location than if you install from a deb package.
/usr/lib vs. /usr/local/lib/.

# Making firmware changes
As for the firmware files (the code that runs on PRUSS), they are moved to /tmp during compilation, but should reside in a sub directory from Redeem.py before compilation.
A recompile of the firmware can be triggered by touching /et/redeem/local.cfg


