Manual Install
==============

To manually add the Debian repository with Replicape and Toggle
packages, add this in a shell on your BeagleBone:

| `` wget -O - ``\ ```http://kamikaze.thing-printer.com/apt/public.gpg`` <http://kamikaze.thing-printer.com/apt/public.gpg>`__\ `` | apt-key add -``
| `` echo ``\ “``deb``\ `` ``\ ```http://kamikaze.thing-printer.com/apt`` <http://kamikaze.thing-printer.com/apt>`__\ `` ``\ ``./``”\ `` >> /etc/apt/sources.list``
| `` apt-get update``

The Kernel in the current image is the 4.1 LTS branch, and it has PRU
support.

Efforts are ongoing to try and use the 4.4 LTS branch for the new
Wireless version of the BeagleBoneBlack.
