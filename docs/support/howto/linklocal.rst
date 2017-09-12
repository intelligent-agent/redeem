Link Local
==========

`Link local` is a way of resolving a url name on your local network.

Some versions of Windows doesn't support this; you may also need this
if your router doesn't do DNS assignment. Install Apple's `bonjour service`__
to autodiscover the BBB on the network.

__ http://bonjour.en.softonic.com/



If you are on a more exotic network, you might have to find your
BeagleBones IP address manually.

Another way is using a USB cable to connect from your computer to the
BeagleBone.
and check your BBBs assigned IP address with ifconfig.



Another method for connecting to your Replicape is via USB and looking
at its assigned IP address with `ifconfig`. And then connect over the
network using that information.

Note that if your
computer may recognize the ethernet but not automatically set an IP that
allows it to talk to the BBB - in which case you should setup a manual
IP on that interface with the address 1.92.168.7.1 and netmask
255.255.255.0
