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

Troubleshooting
---------------

Log into your board with
`SSH <https://mediatemple.net/community/products/dv/204403684/connecting-via-ssh-to-your-server>`__:

::

    ssh root@kamikaze.local

If you want to see the current status for Redeem:

::

    root@kamikaze:~# systemctl status redeem -n 100
    * redeem.service - The Replicape Dameon
       Loaded: loaded (/lib/systemd/system/redeem.service; enabled)
       Active: active (running) since Thu 2016-04-28 15:55:28 UTC; 33s ago
     Main PID: 312 (redeem)
       CGroup: /system.slice/redeem.service
               |-312 /usr/bin/python /usr/bin/redeem
               |-530 socat -d -d -lf /var/log/redeem2octoprint pty,mode=777,raw,echo=0,link=/dev/octoprint_0 pty,mode=777,raw,echo=0,link=/dev/octoprint_1
               |-532 socat -d -d -lf /var/log/redeem2toggle pty,mode=777,raw,echo=0,link=/dev/toggle_0 pty,mode=777,raw,echo=0,link=/dev/toggle_1
               |-534 socat -d -d -lf /var/log/redeem2testing pty,mode=777,raw,echo=0,link=/dev/testing_0 pty,mode=777,raw,echo=0,link=/dev/testing_1
               `-536 socat -d -d -lf /var/log/redeem2testing_noret pty,mode=777,raw,echo=0,link=/dev/testing_noret_0 pty,mode=777,raw,echo=0,link=/dev/testing_noret_1

    Apr 28 15:55:37 kamikaze redeem[312]: 04-28 15:55 root         INFO     Redeem initializing 1.2.2~Predator
    Apr 28 15:55:37 kamikaze redeem[312]: 04-28 15:55 root         INFO     Using config file /etc/redeem/default.cfg
    Apr 28 15:55:37 kamikaze redeem[312]: 04-28 15:55 root         INFO     Using config file /etc/redeem/kossel_mini.cfg
    Apr 28 15:55:37 kamikaze redeem[312]: 04-28 15:55 root         INFO     Using config file /etc/redeem/local.cfg
    Apr 28 15:55:37 kamikaze redeem[312]: 04-28 15:55 root         INFO     -- Logfile configured --
    Apr 28 15:55:38 kamikaze redeem[312]: 04-28 15:55 root         INFO     Found Replicape rev. 00B3
    Apr 28 15:55:39 kamikaze redeem[312]: 04-28 15:55 root         INFO     Cooler connects therm E with fan 1
    Apr 28 15:55:39 kamikaze redeem[312]: 04-28 15:55 root         INFO     Added fan 0 to M106/M107
    Apr 28 15:55:39 kamikaze redeem[312]: 04-28 15:55 root         INFO     Added fan 3 to M106/M107
    Apr 28 15:55:39 kamikaze redeem[312]: 04-28 15:55 root         INFO     Stepper watchdog started, timeout 60 s
    Apr 28 15:55:39 kamikaze redeem[312]: 04-28 15:55 root         INFO     Ethernet bound to port 50000
    Apr 28 15:55:39 kamikaze redeem[312]: 04-28 15:55 root         INFO     Pipe octoprint open. Use '/dev/octoprint_1' to communicate with it
    Apr 28 15:55:40 kamikaze redeem[312]: 04-28 15:55 root         INFO     Pipe toggle open. Use '/dev/toggle_1' to communicate with it
    Apr 28 15:55:40 kamikaze redeem[312]: 04-28 15:55 root         INFO     Pipe testing open. Use '/dev/testing_1' to communicate with it
    Apr 28 15:55:40 kamikaze redeem[312]: 04-28 15:55 root         INFO     Pipe testing_noret open. Use '/dev/testing_noret_1' to communicate with it
    Apr 28 15:55:40 kamikaze redeem[312]: 04-28 15:55 root         INFO     Alarm: Operational
    Apr 28 15:55:40 kamikaze redeem[312]: 04-28 15:55 root         INFO     Watchdog started, refresh 30 s
    Apr 28 15:55:40 kamikaze redeem[312]: 04-28 15:55 root         INFO     Redeem ready
    root@kamikaze:~#
