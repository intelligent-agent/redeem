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

Q: Where can I get help setting up Redeem or Toggle?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

'''A: ''' There are two main channels for community support. One is the
`Thing-Printer
Google+ <https://plus.google.com/communities/104577360369030938514>`__
community. The other is the `Replicape
Slack <http://www.thing-printer.com/wp-login.php?action=slack-invitation>`__
chat. The chat has the main channels `archived
publicly <http://replicape.slackarchive.io/>`__ so you can search for a
previous answer related to your problem.

Q: My steps per mm are wrong/my printer is moving way too far per mm!
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**A:** If you're using the Prusa Calculator on `\| this
site <http://www.prusaprinters.org/calculator/>`__ to figure your steps
per millimeter, keep in mind that under the 'Steps per millimeter -
leadscrew driven systems' section, the Pitch Presets are referring to
threaded rod, not leadscrews. Leadscrews are typically measured by
diameter, pitch, and starts.

If you look at the end of the leadscrew and you see the ends of two
threads, that is a '2-start' leadscrew. If you see 4 threads, it's a
'4-start' leadscrew.

Pitch is the distance between threads. A typical 8mm leadscrew would
have a 2mm pitch.

You multiply your starts by your pitch, to find out how far the
leadscrew would move in one revolution. A TR8\*8 leadscrew, is 8mm in
diameter, has 4 starts, and a 2mm pitch, which means it moves 8mm per
turn. You would need to put 8mm in for the pitch, instead of 1.25mm (the
default setting if you select M8 for the Pitch Preset).

Q: Where did /dev/octoprint\_1 go?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

I'm getting the error: Failed to autodetect serial port, please set it
manually.

Why can OctoPrint not connect to Redeem?

**A:** Chances are, Redeem has either crashed when you restarted it due
to a bad config, or it wasn't reporting “Redeem Ready” when you
restarted OctoPrint. If you restarted Redeem, wait about 10 seconds
before restarting OctoPrint or hitting Connect in OctoPrint. This gives
Redeem enough time to get started and be ready for the connection. If
you want to connect to the BBB, you can run the following to check the
status of Redeem when you restart it:

| ``ssh root@kamikaze.local``
| ``systemctl status -n 100 redeem``

You should see if there is a problem with Redeem.

| On older boards (B3 revisions), the EEPROM may not be updated. has
  instructions on how to update the EEPROM. Pleas note, if you have a
  Rev A4A board, do not run this, as it will brick the Replicape.

Q: Are the stepper drivers integrated into the Replicape, plug in, or external style?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

| If they’re integrated it could be a problem when I manage to fry a
  driver.
| **A:** The stepper drivers are integrated, but the DRV8825’s are very
  hard to fry! They have both temperature protection and over current
  protection, so I have not been able to fry a single one so far! This
  is in contrast with the A4988’s that burn easily.

Q: Will the Replicape hook up to thermocouples?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**A:** I have gotten a few questions about that, so I might extend the
capabilities of the board to allow use of thermocouples. However, the
best way to handle that is to have the external circuitry necessary
closer to the print head. As far as I know, that is the normal practice.
I have it on my list to make a blog post on how to use Thermocouples
with Replicape, but I have not gotten around to making it yet.

Q: Would the board come with the connectors and pins for DIY wire harnesses?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A: There are connector for the large black screw terminals you see on
the end. Most (not all) stepper motors come with four-header connectors
as standard, so they might fit directly on or they might need
re-positioning. Fans mostly come with 2 female pin headers, but they
will likely need extensions. End stops need to be customized and
thermistors also. Sorry for not supplying the cable assemblies yet, but
I might do it in the future. All I can offer for now is some extra info
on the web-page and a link to some suppliers..

Q: Is the Manga going to become available anytime soon?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It would be nice to integrate everything at once.

**A:** Manga Screen 2 has a
`Kickstarter <https://www.kickstarter.com/projects/1924187374/manga-screen-2>`__
going at the moment. We want to get the volume up in order to offer the
screen at a low cost.

Q: Why is it so expensive?
^^^^^^^^^^^^^^^^^^^^^^^^^^

**A:** It’s really not. This is a premium product that uses higher
quality components than most of the other electronics boards. In
addition it has some clever solutions like stepper drivers with over
current protection, programmable stepper driver current, microstepping
controlled via SPI, all mosfets controlled with PWM, drivers on all
MOSFET for keeping the temerature down, 5V and 12V DC-DC converters so
you can use a single 12..24V PSU, EEPROM for identifying the board, high
quality connectors, noise filters on the analog inputs, etc. These
things drive the price of the components, so the Bill Of Materials is at
$96 not including the PCB and assembly. Yes, you can get cheaper
electronics, but a lot of them break down due to bad design choices and
that costs money for a new board, takes time to reassemble the printer
and gives printer down-time.

Q: What is programmable stepper current why do I need it?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**A:** Programmable stepper current means that the chopping current
limit on the stepper motor controllers are set using a Digital to Analog
Converter instead of with a trim-potensiometer which is the normal way
of doing it. For one it gets easier to share settings among printers as
it is loaded from a file at run time and secondly you do not have to
have physical access to the board once it is mounted on your printer
which gives better choice in electronics placement.

Q: What is programmable microstepping and why should I care?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**A:** The stepper motor driver in the DRV8825’s have microstepping down
to 1/32. That means it needs a total of five dip switches or
micocontroller output lines (2^5 = 32) for each stepper motor driver.
That eats PCB real-estate or uC pins which is bad. An alternative is to
use a Serial to parallel converter, and hook that up to the SPI port.
That way, only 4 uC pins are used but you can still control all the 5\*5
= 25 pins that are necessary for accessing all the microstepping
options. In addition, you do not have to have physical access to the
board since the settings for the microstepping is read from a config
file at run time.

Q: What screens can I use with Replicape?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**A:** I’ve only tested Manga Screen and LCD3 cape:
http://elinux.org/Beagleboard:BeagleBone_LCD3, but some users have
reportedly used other screens.

Q: Can I use the Ramps LCD? http://reprap.org/wiki/RAMPS_LCD
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**A:** Not without a lot of integration. By that I mean you have to
either make a cape to support it or you need to manually wire the
necessary pins. You also need to port the software. Probably a great
weekend project, but who has the time : )

Q: How can I make sure my axis are moving correctly?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**A:** The important thing to remember is, when you click on the Control
arrows in OctoPrint, they are moving the print head as if the print bed
is stationary. This is important for printers that move the bed
downward, such as a CoreXY design. If you click the Z Up arrow, the
distance from bed to print head should **increase**. If you have a
printer that shifts the print bed in the Y axis, clicking the Y Up arrow
should move the bed towards you, moving away from the front left corner
of the bed (0,0).

Q: How can I change my homing direction/my system is homing in the wrong direction!
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**A:** First, check the FAQ above and verify that your axis are moving
correctly. Once you are certain they are, in your Redeem local.cfg, find
or add the following section:

| ``[Homing]``
| ``home_speed_x = 0.05``
| ``home_speed_y = 0.05``
| ``home_speed_z = 0.05``
| ``home_speed_h = 0.05 #If you are running a slave stepper``

And add a negative sign in front of the appropriate axis, like so:

`` home_speed_z = -0.05``

This will invert the homing for that axis and make it home to z\_max
instead of z\_min.

Q: My Toggle session doesn't show the model that's printing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**A:** If you uploaded the STL file and used onboard slicing and it's
not showing up, chances are the Toggle REST API needs to be updated. In
the local.cfg for Toggle, add the following, then restart Toggle.

| ``[Rest]``
| ``api_key = *ChangeMeToYourOctoPrintAPIKey*``

Q: How can I rotate my Toggle screen
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**A:** Edit the local.cfg for Toggle, either through the Octoprint
interface, or at the command line. Add the following to the file, then
restart Toggle:

| ``[System]``
| ``rotation = 0``

Q: I come from a Marlin/Repetier/xxx (arduino mega) setup what do I do?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**A:** Well, you could start by looking at this `handy migration
guide <marlin_to_redeem>`__ (still under construction though)

Q: I got my Replicape, but Redeem can't communicate with it
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**A:** Are you powering only through USB? If so, that will be a source
of difficulties. The replicape needs power applied to communicate with
the BBB underneath, the BBB won't power the Replicape. Normally, the
opposite is what happens, with the BBB being powered by the Replicape.
See `Replicape\_rev\_B#Power <Replicape_rev_B#Power>`__ for details of
the error to look for in your system log.

Q: I can't connect the BBB to my network, how do I get updates from online?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**A:** Well, if you don't have a USB Wifi dongle, or Ethernet cable you
can use to connect the BBB to your network at home, you can follow `this
guide <https://elementztechblog.wordpress.com/2014/12/22/sharing-internet-using-network-over-usb-in-beaglebone-black/>`__
to get it online using your PC running linux as a bridge through the
mini-USB cable.

For Windows users, this is a great guide:
https://www.youtube.com/watch?v=D-NEPiZDSx8
