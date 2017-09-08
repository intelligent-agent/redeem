============
Installation
============

The first step to running the Replicape board with Redeem is to install
an OS on the BBB. It is recommended that you download and install the
latest pre-build `Kamikaze image <Kamikaze#Download_Kamikaze>`__ on the
SD card then it will update the BBB image.

Installation
------------

The way this works is you download an image file, extract that onto a
mico SD card and place that SD card in your BeagleBone Black. After some
5 minutes of looking at the logo and drinking coffee, the flashing
procedure is over, you remove power from the BeagleBone, eject the SD
card and re-apply power to the board. If you have `Manga
Screen <Manga_Screen>`__, you should see `Toggle <Toggle>`__ appear on
the LCD. You should also be able to point your browser to
`http://kamikaze.local
http://kamikaze.local <http://kamikaze.local_http://kamikaze.local>`__
which will display a welcome wizard with instructions about how to set
up your Octoprint instance. The rest of the documentation is included in
the `Redeem <Redeem>`__ page or below.

Running from SD card
--------------------

If you want to run the image from the SD card and not overwrite the on
board flash, you need to place the SD card in a computer running Linux
(Windows and MacOS cannot read the card as yet) and edit the file on the
SD card with the path /boot/uEnv.txt. from the partition called Umikaze.
Comment out the last line of the file with a #, the line that starts the
flasher instead of systemd.

Flashing procedure
------------------

Once the SD card is inserted in the SD card slot of the BBB, hold down
the “boot” button and apply power. If you have a Manga Screen installed,
the Kamikaze splash screen will appear within 3 seconds. After 10-5
seconds, the 4 lights on the BBB will flash in a “Night rider” pattern
(also called cylon leds). Once the flashing procedure is done, after
about 15 minutes, the board will power down. Remove power, eject the
SDcard and re-apply power. The first time the BBB boots up after
removing the SD card, it will run a script to compile the device tree
overlays into the kernel and then it will reboot.