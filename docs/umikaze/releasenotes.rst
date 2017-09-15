Release notes
=============

..  versionadded:: 2.1.1

-  BeagleBone Black Wireless support
-  Staging branch of Redeem installed by default
-  TI C PRU compilation software packages (for new PRU firmwares in use on the development branch of redeem)
-  CPU governor fixed to “performance” by default, reserves computational power for printing
-  Octoprint version number now the official release version
-  Slic3r command line, allowing the use of the Slic3r plugin in OctoPrint

..  note::

    Octoprint and the /etc/kamikaze-release file will show Umikaze
    2.1.1 RC2, however this is an oversight and will not impact
    functionality

..  warning::

    Integrated backup & restore of config files is not included. Any upgrade
    from previous versions will destroy local config files. Tools for upgrade
    are forthcoming.


Changes
-------

- Release 2.1.1 unfortunately cannot fit in the eMMC of the
  2GB beaglebones anymore - despite best efforts to keep the size down,
  the added requirements for Redeem make it just too large to fit.

  Efforts are ongoing to try and reduce footprint while maintaining
  functionality, but in the meantime it is recommended that you run
  Umikaze 2.1.1 off the microSD card if you use a 2GB BeagleBone.

- Previous PRU firmware has been rewritten to fix speeds and accelerations;
  lower values physically than what was defined in the configuration. This
  has been fixed.

  Any previous speed or acceleration values will result in much higher
  acceleration and higher top speeds! It is recommended that values
  be reduced by half to two-thirds of previous values initially then
  re-tune them to your machine.

  This backwards compatibility is unfortunate but guarantees a true
  correlation between configuration values and actual accelerations
  and speeds actuated by your printers, meaning if you had a working
  configuration using a RAMPS or other board, similar values should
  now be adequately close with Redeem.

- New and deprecated configuration parameters:

::

    [Delta]
    # DEPRECATED
    Hez = 0.0
    Ae  = 0.026
    Be  = 0.026
    Ce  = 0.026
    A_tangential = 0.0
    B_tangential = 0.0
    C_tangential = 0.0

    # NEW
    A_angular = 0.0
    B_angular = 0.0
    C_angular = 0.0

    [Planner]
    # DEPRECATED
    max_length = 0.001
    min_speed_x = 0.005
    min_speed_y = 0.005
    min_speed_z = 0.005
    min_speed_e = 0.01
    min_speed_h = 0.01
    min_speed_a = 0.01
    min_speed_b = 0.01
    min_speed_c = 0.01

    # NEW
    # if total buffered time gets below (min_buffered_move_time) then wait
    # for (print_move_buffer_wait) before moving again, (ms)
    min_buffered_move_time = 100

- New PRU firmwares require additional software packages to
  compile properly (and they get compiled and sent to the PRU each time
  redeem starts or the endstop configurations are modified).


Upgrading
---------

From Kamikaze 2.0.8
~~~~~~~~~~~~~~~~~~~

Tested thoroughly for several weeks by multiple users on cartesian, delta and
core XY geometries. Few negative reports were made, and most of those
pertained to Redeem bugs which were quickly fixed.

To backup your configuration you'll need either: - a USB drive of 4GB or
more that you can plug in while maintaining network connection (i.e. USB
hub if you have a wifi dongle) - a microSD card of 4GB with an empty
file system and that **doesn't** contain a BBB image on it.

You'll also need a little bit of patience, and a computer where you can
run SSH to connect to the BBB.

First you need to tell Kamikaze where to find the SD card, and which
folder it should be made accessible as. Linux folks will know this as a
“mount command”.

The SD card on the BBB (and BBBW) should always have the same device
name, so the following command should work:
``mount /dev/mmcblk0p1 /mnt/`` Now, any file or folder added, created or
removed in /mnt/ will be on the SD card.

Manual backup is required as 2.1.1 does not have this as part of upgrading:

- **Redeem configuration** ``cp -r /etc/redeem/ /mnt/redeem_cfg_backup``
  will copy the files from ``/etc/redeem/`` into a new folder on the
  SD named ``redeem\_cfg\_backup``.

- **OctoPrint configuration and Timelapses** ``cp -r /home/octo/.octoprint/ /mnt/octoprint_cfg_backup``
  will copy the Octoprint files (including timelapses) over.

- **STL and GCode files uploaded to OctoPrint** ``cp -r /usr/share/models /mnt/models``
  will copy the files you've uploaded to Octoprint.

- **Network settings** Due to change in network configurator, settings can not be
  ported. If you've defined IPtables rules, those can be transferred.


From Kamikaze 2.1.0
~~~~~~~~~~~~~~~~~~~

Please backup your files as per the instructions for Kamikaze 2.0.8
users above.

Network settings are compatible; to back those up as well:

- **NetworkManager settings** ``cp -r /etc/NetworkManager /mnt/NetworkManager``
  will copy the network configuration settings you have saved

Restoring
---------

Restoring Network Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``nmtui`` as a simple text interface network configuration tool, eliminating complicated syntactical commands

This is assuming that you have managed to connect to your BBB after the
upgrade (either via ethernet or USB-ethernet tether), and haven't copied
the files into the image SD card first. This step is only helpful if you
were using Kamikaze 2.1.0 prior to the upgrade.

Mount the USB drive or SD card back in after being logged in via SSH to
the BBB.

-  If using an SD card, mount it with ``mount /dev/mmcblk0p1 /mnt/``
-  If using a USB flash drive, mount it with ``mount /dev/sdb1 /mnt``

Then copy the NetworkManager files back in place with:
``cp -r /mnt/NetworkManager /etc/``

Restoring OctoPrint Configuration & TimeLapses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This one needs to be done right after you restore the network
communication. This is because OctoPrint itself has an internal upgrade
mechanism and if you use old configuration files, OctoPrint reads them,
then just upgrades them after having loaded the values it can from the
files on disk. Cool, right? Thank Gina over at
`octoprint.org <http://octoprint.org>`__. We're still trying to catch to
all the awesome bells and whistle's she's managed to build into
OctoPrint!

Assuming you've mounted your SD card or backup drive as indicated in
`Restoring Network
Configuration <Release_notes_Umikaze_2.1.1#Restoring_Network_Configuration>`__,
follow this simple step to restore OctoPrint configurations:

``cp -r /mnt/octoprint_cfg_backup /home/octo/.octoprint && chown -R octo:octo /home/octo``

Then restart octoprint, either through SSH with
``systemctl restart octoprint``, or via the OctoPrint interface if it's
available to you.

Restoring Redeem Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

What's important here is to copy only your local.cfg file, and **not**
all the files. The reason for this is that Redeem's default.cfg file has
changed since the last version you had installed, and you don't want to
feed it a file without all the values it expects, and some it doesn't
use anymore. So.

The best way is to go through the octoprint Redeem plugin tab in the
settings panel, and hit the “edit” icon next to the local.cfg file. Copy
the contents of the local.cfg file you had backed up into, save, make
sure you select the printer geometry type you need in the list below by
clicking the star, and then press the blue “Restart Redeem” button.
After a minute or so you should be able to reconnect OctoPrint to Redeem
and start moving your printer again.

That said, make sure you have your SD or USB drive inserted and mounted
as in `Restoring Network
Configuration <Release_notes_Umikaze_2.1.1#Restoring_Network_Configuration>`__
and then follow these simple steps:

``cp /mnt/redeem_cfg_backup/local.cfg /etc/redeem/ && chown -R octo:octo /etc/redeem``

Restoring the STL and GCode models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Again make sure you have your SD card or USB drive inserted and mounted
as in `Restoring Network
Configuration <Release_notes_Umikaze_2.1.1#Restoring_Network_Configuration>`__.

Then simply run
``cp -r /mnt/models /usr/share/ && chown -R octo:octo /usr/share/models``

Voila, you're done!

To cleanly unmount your SD card or USB drive (i.e. to make sure all
files are properly copied in place and not risk damaging the filesystem
on the removable storage device), execute ``umount /mnt/``. Wait until
the command finishes, and once it's done, you can remove the USB or SD
drive from the BBB and start discovering the changes we've made.

Copying NetworkManager settings onto the Umikaze flashed image
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You'll need to be able to read the files on the flashed SD card. OS X
and Linux will have no trouble doing this, Windows will be slightly more
of a challenge. The SD card uses an ext3 file system, which Windows
doesn't natively read. However this
`tutorial <http://www.techrepublic.com/blog/tr-dojo/enable-the-mounting-of-ext2-3-file-systems-on-a-windows-machine/>`__
will help you achieve that.

Once you see the files on the SD card, copy the entire NetworkManager
folder from your backup drive to within the ``etc`` folder on the
Umikaze image. You will want to overwrite any files and folders
previously existing there.

Creating a NetworkManager setting on the Umikaze flashed image
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Assuming you've been using 2.0.8 for a while, you may be wondering “how
in the world will I get Umikaze connected if I can't hook up a cable to
my BBB?” Fear not. Two ways for this exist.

-  The simpler, easier way, is that if you have a spare BBB lying
   around, you can edit one line of one file on the SD card so it will
   boot from SD instead of flash from SD. This file is ``boot/uEnv.txt``
   and the line to edit is the very last one in the file - simply add a
   # in front of the command. Now, you can boot the spare BBB off the SD
   card, set the wifi network you want using ``nmtui``, make sure you're
   connected to the 'net with it, and then shut it down. Pull out the
   SD, insert it into your computer, open up the ``boot/uEnv.txt`` file
   again, remove the # sign you inserted on the very last line, save,
   remove the SD card and flash away.

-  The slightly more complex way, because you'll need to create a
   configuration file instead of use the tools to set one up for you,
   means creating a file and editing it on the SD card. You'll need to
   be very careful about following the right syntax and not having
   typos. You'll need to create a file in this folder:

``etc/NetworkManager/system-connections``

| ``[connection]``
| ``id=``\
| ``uuid=8836d6ae-0218-4c96-a204-247109ab820a``
| ``type=wifi``
| ``permissions=``
| ``secondaries=``
| ``[wifi]``
| ``mac-address=``\
| ``# you can get your BBB's mac address by running ifconfig on your BBB and looking for the entry with the IP of your network.``
| ``mac-address-blacklist=``
| ``mac-address-randomization=0``
| ``mode=infrastructure``
| ``seen-bssids=``
| ``ssid=``\
| ``[wifi-security]``
| ``auth-alg=open``
| ``group=``
| ``key-mgmt=wpa-psk``
| ``pairwise=``
| ``proto=``
| ``psk=``\
| ``[ipv4]``
| ``dns-search=``
| ``method=auto``
| ``[ipv6]``
| ``addr-gen-mode=stable-privacy``
| ``dns-search=``
| ``method=auto``
