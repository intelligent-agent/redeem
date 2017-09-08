Connecting
==========

There are several ways to connect your computer to the BeagleBone Black.
If you have a router or switch, simply use a network cable and connect
your BeagleBone to that. The BeagleBone should start to answer pings on
the `https://en.wikipedia.org/wiki/Link-local\_address
link-local <https://en.wikipedia.org/wiki/Link-local_address_link-local>`__
address right away:

::

    ping kamikaze.local

If you are on a more exotic network, you might have to find your
BeagleBones IP address manually.

Another way is using a USB cable to connect from your computer to the
BeagleBone. The BeagleBone has ethernet over USB that has a static IP
address of 192.168.7.2. You can then log in with ssh:

::

    ssh root@192.168.7.2

and check your BBBs assigned IP address with ifconfig. Note that if your
computer may recognize the ethernet but not automatically set an IP that
allows it to talk to the BBB - in which case you should setup a manual
IP on that interface with the address 1.92.168.7.1 and netmask
255.255.255.0

**Note for Windows users:** you'll need to install Apple's `bonjour
service <http://bonjour.en.softonic.com/>`__ to autodiscover the BBB on
the network, if your router/modem doesn't do DNS assignment (or if
you're using USB). Furthermore, for ssh on windows, it is recommended to
use `PuTTY <http://www.putty.org/>`__


Username/password
-----------------

For SSH:

::

    root: kamikaze

|
| There is another user existing, which is

::

    ubuntu: temppwd

That is the default user password which can use sudo. If you are not on
a secure and private network, it is highly advised to change the
password for both accounts! Do this by SSH-ing in as the user you want
to change the password of and running the command

``passwd``

Note that these user passwords are completely separated from the
octoprint users you setup during the setup wizard for access control!


