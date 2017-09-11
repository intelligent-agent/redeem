Kamikaze
========

..  figure:: ./images/kamikaze_header.png
    :figclass: inline


..  contents:: Table of Contents
    :depth: 2
    :local:

..  toctree::
    :numbered:

Kamikaze is a complete Linux distribution based on Debian Jessie (8),
alternatively Stretch (9) for Kamikaze 2.0. It has all the necessary
software for running :doc:`/replicape` to control your 3D
printer.

The way this works is you download an image file, extract that onto a
mico SD card and place that SD card in your BeagleBone Black. After some
5 minutes of looking at the logo and drinking coffee, the flashing
procedure is over, you remove power from the BeagleBone, eject the SD
card and re-apply power to the board. If you have :doc:`/magnascreen`,
you should see :doc:`/toggle` appear on the LCD. You should also be able
to point your browser to http://kamikaze.local  which will display a
welcome screen with some information about how to set up your printer.

The current (stable) version of Kamikaze.

Kamikaze 2.0 is now available for download. With version 2.0, the way
the image is created has changed. The image is now made starting from
the official IoT Debian distribution for BeagleBone, and altered to be
great for 3D-printing. Redeem, Toggle and OctoPrint is now installed
by forking the git repository and installing from source. This makes
hacking very easy, and also enables updates to be monitored from
within OctoPrints own software update system.

`Kamikaze-2.0.8-2016-10-16.img.xz <https://github.com/eliasbakken/Kamikaze2/releases/download/v2.0.8/Kamikaze-2.0.8-2016-10-17.img.xz>`_

Here is the MD5 sum for it: a438f453be3a390b6bf51ad719ad65a9

The size is 1.1GB (1123946180 B) compressed, but expands to a 3.2GB partition, suitable for a 4GB SD card.


Username/password
-----------------

| For SSH: debian/temppwd
| Also: root/“no password”
| Note: Root access with no passord is a big security risk and not for
  production use. If your printer has an external IP, disable root
  access.

Burn image
----------

| Once you have the BBB-flasher downloaded to your computer, you can
  transfer it to a microSD card (not included) in the normal manner.
| Go to `http://www.etcher.io/ <http://www.etcher.io/>`__ and download
  the app for your OS.

Linux
~~~~~

For Linux, make sure you make the app executable and start it as root:

::

    cd ~/Downloads
    chmod +x Etcher-linux-x64.AppImage
    sudo ./Etcher-linux-x64.AppImage

Windows
~~~~~~~

It's a normal program installer. Install it and run it.

OS X
~~~~

It's a normal installer, just drag the app into the application folder.

Starting up
-----------

You should see the app appear, similar to this:

..  figure:: ./images/etcher.png
    :figclass: inline

Follow the instructions from the app, briefly:

1. Hit “select image” and find the image you previously downloaded called " BBB-eMMC-flasher-kamikaze-YYYY-MM-DD-4gb.img.xz".

1. Insert a 4GB micro SD card in your SD card reader slot. The card should be detected by the app.

3. Hit flash, and wait for it to finish.

I've also made a quick video on how to do this procedure:

..  raw:: html

    <iframe width="560" height="315" src="https://www.youtube.com/embed/23Id20_8hWs" frameborder="0" allowfullscreen></iframe>


Running Kamikaze from SD card
-----------------------------

If you want to run the image from the SD card and not overwrite the on
board flash, you need to place the SD card in a computer and edit the
file on the SD card with the path /boot/uEnv.txt. from the partition
called Kamikaze. Comment out the last line of the file, the line that
starts the flasher instead of systemd.

Flashing procedure
------------------

Once the SD card is inserted in the SD card slot of the BBB, hold don
the “boot” button and apply power. If you have a Manga Screen installed,
the Kamikaze splash screen will appear within 3 seconds. After 10-5
seconds, the 4 lights on the BBB will flash in a “Night rider” pattern
(also called cylon leds). Once the flashing procedure is done, after
about 15 minutes, the board will power down. Remove power, eject the
SDcard and re-apply power. The first time the BBB boots up after
removing the SD card, it will run a script to compile the device tree
overlays into the kernel and then it will reboot.

Troubleshooting
---------------

Make sure:

#. The microSD card you are using is 4GB.
#. All the lights light up at the end of the flashing procedure.
#. You remove the card after the flashing procedure is done.
#. During the first boot, you leave it powered on for a few minutes. On first boot, some scripts will run, then a reboot will happen.

Getting started
---------------

..  raw:: html

    <iframe width="560" height="315" src="https://www.youtube.com/embed/BKb28fJx26I" frameborder="0" allowfullscreen></iframe>


Ways to connect
---------------

There are several ways to connect your computer to the BeagleBone Black.
If you have a router or switch, simply use a network cable and connect
your BeagleBone to that. The BeagleBone should start to answer pings on
the `link-local <https://en.wikipedia.org/wiki/Link-local_address_link-local>`_ address right away::

    ping kamikaze.local

If you are on a more exotic network, you might have to find your
BeagleBones IP address manually. One way is using a USB cable to connect
from your computer to the BeagleBone. The BeagleBone has ethernet over
USB that has a static IP address of 192.168.7.2. You can then log in
with ssh::

    ssh root@192.168.7.2

and check your BBBs assigned IP address with ifconfig.

**Note for Windows users:** you'll need to install Apple's `bonjour
service <http://bonjour.en.softonic.com/>`_ to autodiscover the BBB on
the network, if your router/modem doesn't do DNS assignment (or if
you're using USB). Furthermore, for ssh on windows, it is recommended to
use `PuTTY <http://www.putty.org/>`_.

Quirks
------

The first time Kamikaze boots, the index file for the kernel objects is
recreated and the necessary permissions for Octoprint are run.
Therefore, a reboot is required for the board to boot as expected.

If you have Manga Screen and would like to avoid the blinking cursor
screwing up your Toggle, you can disable the cursor from the command
line of BeagleBone. Disable console cursor::

    echo 0 > /sys/class/graphics/fbcon/cursor_blink

Upgrading packages
------------------

Since this is a Debian system, packages can be upgraded with apt.

::

    apt-get update
    apt-get upgrade
    apt-get install toggle
    apt-get install python-octoprint-toggle

Please note that since this also upgrades the SSH daemon, which will
kick the user out during the upgrade process. If that happens, you need
to SSH back in, and continue the process:

::

    dpkg --configure -a

Wifi
----

Kamikaze uses Connman for handling connections. Typically, you will
perform the following actions (taken from the Arch wiki): For protected
access points you will need to provide some information to the ConnMan
daemon, at the very least a password or a passphrase. The commands in
this section show how to run connmanctl in interactive mode, it is
required for running the agent command. To start interactive mode simply
type::

    $ connmanctl

You then proceed almost as above, first scan for any Wi-Fi technologies::

    connmanctl> scan wifi

To list services::

    connmanctl> services

Now you need to register the agent to handle user requests. The command is::

    connmanctl> agent on

You now need to connect to one of the protected services. To do this
easily, just use tab completion for the wifi\_ service. If you were
connecting to OtherNET in the example above you would type::

    connmanctl> connect wifi_dc85de828967_38303944616e69656c73_managed_psk

The agent will then ask you to provide any information the daemon needs
to complete the connection. The information requested will vary
depending on the type of network you are connecting to. The agent will
also print additional data about the information it needs as shown in
the example below::

     Agent RequestInput wifi_dc85de828967_38303944616e69656c73_managed_psk
       Passphrase = [ Type=psk, Requirement=mandatory ]
       Passphrase?

Provide the information requested, in this example the passphrase, and
then type::

    connmanctl> quit

If the information you provided is correct you should now be connected
to the protected access point.

Webcam
------

Webcam streaming has been tested with Logitech C270. Most of this is
from `Setup On BeagleBone Black <https://github.com/foosel/OctoPrint/wiki/Setup-on-BeagleBone-Black-running-%C3%85ngstr%C3%B6m#webcam>`_.
To enable webcam streaming, strting with the latest image, try this::

    apt-get update
    apt-get install cmake libjpeg-dev

Install mjeg streamer::

     cd /usr/src/
     git clone https://github.com/jacksonliam/mjpg-streamer
     cd mjpg-streamer/mjpg-streamer-experimental
     sed -i 's:add_subdirectory(plugins/input_raspicam):#add_subdirectory(plugins/input_raspicam):' CMakeLists.txt
     make
     make install
     ./mjpg_streamer -i "./input_uvc.so" -o "./output_http.so" &


The stream should be available through http://kamikaze.local:8080/?action=stream

To integrate this in Octoprint::

    nano /home/octo/.octoprint/config.yaml

Add this to the webcam section::

    webcam:
       stream: http://kamikaze.local:8080/?action=stream
       snapshot: http://kamikaze.local:8080/?action=snapshot
       ffmpeg: /usr/bin/avconv


Restart octoprint::

    systemctl restart octoprint

To make a service for this, drop a line in udev::

    echo 'KERNEL==``\ “``video0``”\ ``, TAG+=``\ “``systemd``”\ ``' > /etc/udev/rules.d/50-video.rules

create mjpg.service::

    nano /lib/systemd/system/mjpg.service

Copy/paste this in mjpg.service file::

    # /lib/systemd/system/mjpg.service
    [Unit]
    Description=Mjpg streamer
    Wants=dev-video0.device
    After=dev-video0.device

    [Service]
    ExecStart=/usr/local/bin/mjpg_streamer -i "/usr/local/lib/mjpg-streamer/input_uvc.so" -o "/usr/local/lib/mjpg-streamer/output_http.so"

    [Install]
    WantedBy=basic.target

Enable service::

    cd /lib/systemd/system/
    systemctl enable mjpg.service

Install Octoprint plugin
------------------------

Chose your plugin at this page: http://plugins.octoprint.org/by_name/

Take a URL source, and clone it on your BBB::

     cd
     git clone "URL source"

Install plugin::

     cd "your-plugin-folder"
     python setup.py install

Restart Octoprint::

    systemctl restart octoprint.service

System commands
---------------

If you want to be able to shutdown and restart your BBB via the
webinterface, you'll first have to add a **sudo** and **systemctl** rule
for octo user::

     cat > /etc/sudoers.d/octoprint-shutdown
     octo ALL=NOPASSWD: /sbin/shutdown
     <ctrl+d>
     cat > /etc/sudoers.d/octoprint-systemctl
     octo ALL=NOPASSWD: /sbin/systemctl
     <ctrl+d>

Copy ``systemctl`` to ``/sbin``::

    cp /bin/systemctl /sbin/

Then add the following lines to your `/home/octo/.octoprint/config.yaml` system::

     actions:
     - action: Restart Redeem
       command: sudo systemctl restart redeem
       name: Restart Redeem
     - action: Restart Octoprint
       command: sudo systemctl restart octoprint
       name: Restart Octoprint
     - action: Shutdown
       command: sudo shutdown -h now
       name: Shutdown
     - action: Reboot
       command: sudo shutdown -r now
       name: Reboot

After restarting and reloading OctoPrint, this should add a System menu
to the top right where you'll find the four commands.

Known problems
--------------

-  Uploading local.cfg via Octoprint Redeem plugin renders an empty file the first time.
-  Blinking cursor over Toggle
-  The Kamikaze logo does not show up during eMMC flashing. Purely cosmetic.

Manual installation of package feed
-----------------------------------

To manually add the Debian repository with Replicape and Toggle
packages, add this in a shell on your BeagleBone::

     wget -O - http://kamikaze.thing-printer.com/apt/public.gpg | apt-key add -
     echo "deb http://kamikaze.thing-printer.com/apt ./" >> /etc/apt/sources.list
     apt-get update

The Kernel in the current image is 4.1.0, and it has PRU support. There
is an effort in moving from UIO based kernel drivers to the newer rproc
framework. In order to use Redeem with this newer kernel, you need to
install a kernel with PRU support. All kernels from 4.0.0 should have
that.

With the new kernel, you can install Redeem (1.0.4 on Jessie)::

    apt-get install redeem

Source files
------------

Kamikaze2 is based on the official BeagleBone distribution of Debian. It
adds some additional packages, specifically Redeem, Octoprint,
CuraEngine, Toggle and the necessary Cogl and Clutter packages for
making that work. Here are the source files: https://github.com/eliasbakken/kamikaze2

Attributions
------------

OctoPrint is the brainchild of Gina Häußge, license AGPL and hosted here: http://octoprint.org/

CuraEngine is developed and maintained by Ultimaker and has the AGPL V3 license. See the git repo for details: https://github.com/Ultimaker/CuraEngine
