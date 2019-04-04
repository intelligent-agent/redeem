```
     _/_/_/                    _/                                     
    _/    _/    _/_/      _/_/_/    _/_/      _/_/    _/_/_/  _/_/    
   _/_/_/    _/_/_/_/  _/    _/  _/_/_/_/  _/_/_/_/  _/    _/    _/   
  _/    _/  _/        _/    _/  _/        _/        _/    _/    _/    
 _/    _/    _/_/_/    _/_/_/    _/_/_/    _/_/_/  _/    _/    _/     
```

Replicape is an attachment for BeagleBone to control control 3D printers and CNC machines, such as routers, lathes and mills.

Redeem is its firmware; it accepts g-codes and translates them into coordinates for your device.

## Software features

- Acceleration with corner speed prediction
- Printer settings loaded from files
- Controllable via OctoPrint, ethernet, USB or MagnaScreen
- Written in python for extensibility
- Optimized for BeagleBone's secondary processing units
- Extendable plugin architecture

## Documentation

[http://wiki.thing-printer.com/](Intelligent-Agent Wiki)

## Installation options

### BeagleBone image

Umikaze (based on Ubuntu 18.04.2 LTS)

### Source install

** WARNING **: The current `master` branch is considered stable, though not yet released while we integrate a few more features to release 2.2.1.
As such, please note that as of this latest change to the master branch, you should be building Redeem off a platform similar to that built by the [https://github.com/intelligent-agent/Umikaze](Umikaze) 
[https://github.com/intelligent-agent/Umikaze/blob/master/Packages/install_redeem](Redeem build script).

The build script will not run as a standalone, however it does include all dependency installations and virtual environment setup, as well as inclusion of the systemd service integration.
