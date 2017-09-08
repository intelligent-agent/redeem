Troubleshooting
===============

MOSFETS turn on and stay on until redeem actually starts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This can be addressed with a patched Uboot, in which case **you will see
the mosfets on for a few seconds until the boot reinitializes** the pin
outputs to low until Redeem can take over.

Troubleshooting
---------------

| Make sure:
| # The microSD card you are using is 2GB or more.

#. All the lights light up at the end of the flashing procedure.
#. You remove the card after the flashing procedure is done.
#. During the first boot, you leave it powered on for a few minutes. On
   first boot, some scripts will run, and Octoprint will take a while to
   start.
#. If you're not planning on using USB networking you'll need to setup
   wifi following the instructions in
   `Kamikaze\_2\_1#Wifi <Kamikaze_2_1#Wifi>`__




Quirks
------

The first time Umikaze boots, the index file for the kernel objects is
recreated and the necessary permissions for Octoprint are run. It can
take a while, please be patient.

If you have Manga Screen and would like to avoid the blinking cursor
screwing up your Toggle, you can disable the cursor from the command
line of BeagleBone. Disable console cursor:

`` echo 0 > /sys/class/graphics/fbcon/cursor_blink``