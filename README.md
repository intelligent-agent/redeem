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

[intelligent-agent.github.io](http://intelligent-agent.github.io)

## Installation options

### BeagleBone image

Umikaze (based on ubuntu 16.03.04)

### Debian package

```
wget -O - http://kamikaze.thing-printer.com/apt/public.gpg | apt-key add -
echo "deb [arch=armhf] http://kamikaze.thing-printer.com/apt ./" >> /etc/apt/sources.list
apt-get update
apt-get install redeem
```

### Source install

```
apt-get install swig python-smbus
mkdir -p /usr/src
cd /usr/src
git clone https://github.com/intelligent-agent/redeem.git
cd redeem
make install
mkdir -p /etc/redeem
cp configs/* /etc/redeem
cp data/* /etc/redeem
```

Other dependencies: [source install docs](https://intelligent-agent.github.io/redeem/replicape/redeem.html#from-source)
