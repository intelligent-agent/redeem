:::python
                                                                     
        _/_/_/                    _/                                     
       _/    _/    _/_/      _/_/_/    _/_/      _/_/    _/_/_/  _/_/    
      _/_/_/    _/_/_/_/  _/    _/  _/_/_/_/  _/_/_/_/  _/    _/    _/   
     _/    _/  _/        _/    _/  _/        _/        _/    _/    _/    
    _/    _/    _/_/_/    _/_/_/    _/_/_/    _/_/_/  _/    _/    _/     


Redeem is the Replicape Daemon that accepts G-codes and turns them into coordinates on 
your 3D-printer. It's similar to Marlin and Teacup, only it's taylor made for Replicape and it's written in Python. 

Software features:  
- Accelleration with corner speed prediction.  
- Printer settings loaded from file  
- Controllable via ethernet, USB, printer display.   


Wiki: http://wiki.thing-printer.com/index.php?title=Redeem

Ipk packets (for Angstrom/Opkg) are available: 
  http://feeds.thing-printer.com/feeds/v2014.06/ipk/eglibc/armv7at2hf-vfp-neon/machine/beaglebone/

Installation:  
You can clone this repository directly on your BBB:  
  ssh root@192.168.7.2  
  cd /usr/src  
  git clone https://intelligentagent@bitbucket.org/intelligentagent/redeem.git  
Make sure gcc, swig, python-dev, binutils and g++ is installed before compiling the native path planner.  
  opkg install swig python-dev gcc binutils g++  

Compile the native path planner module:  
  cd /usr/src/redeem/software/path_planner  
  python setup.py install  
  chmod +x /usr/src/redeem/software/Redeem.py

Compile the device tree overlay:  
  dtc -O dtb -o /lib/firmware/BB-BONE-REPLICAP-0A4A.dtbo -b 0 -@ /usr/src/redeem/Device_tree/BB-BONE-REPLICAP-00A4.dts
    
Enable the redeem service:  
  cp /usr/src/redeem/systemd/redeem.service /lib/systemd/system/redeem.service  
  systemctl enable redeem.service
  systemctl start redeem.service

Development: 
  Try to be PEP8 compliant: http://legacy.python.org/dev/peps/pep-0008/
