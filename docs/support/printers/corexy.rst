Core XY
=======

This is a first pass at documenting how to set up a Replicape board to
run a CoreXY printer.

Assumptions
-----------

-  I'm going to assume you have a basic amount of Clue and can find your
   way around at the command line for this pass.
-  I can go back later and flesh it out with more detail.

I'm not going to cover how to install the software, as that's already
explained over at the `Thing-Printer
Wiki <http://wiki.thing-printer.com/index.php?title=Kamikaze>`__

Prerequisites
-------------

You should gather the following information:

-  Stepper motor specs, specifically the maximum current they can handle
-  Print bed dimensions
-  Limit switch locations
-  Homing directions (will be related to the limit switch locations
   above)

Background information
----------------------

BeagleBone Black / Wireless (BBB)

-  System board that the entire stack runs on.

Replicape Board

-  Runs Redeem ('firmware')
-  Runs Toggle ('display controller')
-  Runs OctoPrint ('print controller')

Theory of Operation
-------------------

Once you have the software installed,updated, and running, you connect
to the OctoPrint software that is running on the BBB and do the initial
setup on it.

-

   -  Need to expand this later

As you step through the setup:

-  Recommended that you keep Access Control Enabled for security
   reasons.
-  Set your print bed dimensions
-  Axis speeds can be left at the defaults, as they only control the
   manual movements that you make through OctoPrint.

Once OctoPrint is set up, log in if you're not already (upper right
corner).

Click on the Settings wrench at the top, near the login button.

At the bottom of the page that comes up, click on the Redeem Plugin
option.

There's several items on this page you need to be aware of and how they
interact with each other.

Configuration Order
-------------------

Redeem uses several config files.

-  local.cfg

   -  Top level config file. The system looks here first.
   -  This file can be directly edited in the Redeem Plugin interface in
      OctoPrint.
   -  If it doesn't find what it needs, it falls through to...

-  printer.cfg

   -  The system looks here if it doesn't find a needed config item in
      the local.cfg file
   -  Has model specific configuration info. Look through the list and
      find a file that is at least similar to your printer, then click
      the star on the right to set it as the preferred config.
   -  If you're setting up a CoreXY design, you'll want to select the
      maxcorexy.cfg profile

-  default.cfg

   -  This is the 'fallback' if the system doesn't find the needed
      information in any of the other config files.
   -  default.cfg has all options, and they are configured with sane
      defaults.

Any changes you need to make should be made in the local.cfg file. Any
option you set in there, will override the other files. Keep your edits
to the local,cfg file, as printer.cfg and default.cfg may be overwritten
on software upgrades

One suggestion is to view the maxcorexy.cfg and copy/paste the entire
cfg into the local.cfg, then make your edits there.

local.cfg
---------

Values in this are in meters, or meters/sec

``offset_x/y/z``

These are the offset of the limit switch from 0,0,0. If you are homing
to X\_Minimum, Y\_Minimum, and Z\_Minimum, these should all be 0.0. If
you are homing to the Maximum on an axis (for example, Y\_Maximum), then
this will be the distance from Maximum to 0

Axis Naming

-  Axis in the config are named for the terminal they're connected to on
   the board. Typically, X, Y, and Z are connected to the appropriate
   axis, E is connected to the Extruder, and H is usually a second
   Extruder or a second stepper that is slaved to another axis

Geometry
~~~~~~~~

This section defines the print bed dimensions and the limit switch offsets

::

    axis_config = 2 #This tells Redeem you're running a CoreXY machine (more info in default.cfg)
    travel_x = 0.250 #X dimension in meters (for this entry, the print bed is 250mm wide)
    travel_y = 0.150 #Y dimension in meters ( 150mm wide )
    travel_z = 0.300 #Z dimension in meters ( 300mm vertical )
    offset_x = 0.000 #X homes to X_Minimum, so there is no offset for it
    offset_y = 0.150 #In this example, Y homes to Y_Maximum, so there is an offset to tell Redeem where 0 is for the Y Axis.
    offset_z = 0.0 #Z homes to Z_Minimum, so no offset for it

Steppers
~~~~~~~~

This section defines your stepper motors. Setting 6 is 1/32 stepping.

::

    microstepping_x = 6
    microstepping_y = 6 
    microstepping_z = 6
    microstepping_e = 6
    microstepping_h = 6

Current in amps to run each stepper at. Anything above 0.5 will require
a cooling fan on the Redeem board. Do not go above the max rating for
your stepper (from the Prerequisite section above) or 1.2A (whichever is
lower). Starting at about 0.4 is a good starting point. If the motors
are running hot after a print, you should lower the current. If you are
skipping steps, raise the current. It is STRONGLY recommended that you
install heat sinks on the TMC2100 driver chips.

::

    current_x = 0.4 
    current_y = 0.4 
    current_z = 0.4 
    current_e = 0.4
    current_h = 0.4

Steps per millimeter for the stepper. No microstepping is used here,
that is defined above in the microstepping_* option:

::

    steps_pr_mm_x = 5.0 
    steps_pr_mm_y = 5.0
    steps_pr_mm_z = 25
    steps_pr_mm_e = 10
    steps_pr_mm_h = 25

If your steppers are whining/singing, set this to 0. If you are having
“weird” problems with missed steps at low speeds, power supply fuses
blowing, or other strangeness, try “slow” decay. If you want to try for
faster top speeds, or are having problems with missed steps at high
speeds, try “fast”.

::

    slow_decay_x = 0 
    slow_decay_y = 0 
    slow_decay_z = 0
    slow_decay_e = 0
    slow_decay_h = 0

Direction for the steppers to turn. If you need to reverse a stepper,
just set it to -1. Your steppers should be plugged in the same way
(black wire to Pin 1 or Pin 4) and just control your direction here. If
the majority of your settings here are -1, power down and flip the
connectors 180 degrees

::

    direction_x = 1 
    direction_y = 1 
    direction_z = 1 
    direction_e = -1 
    direction_h = 1

A stepper controller can operate in slave mode, meaning that it will
mirror the position of the specified stepper. Typically, H will mirror Y
or Z, in the case of the former, write this: slave\_y = H.

in_use_h = True # Enable the slave stepper driver 
slave_z = H

Heaters
~~~~~~~

::

     # List of `temperature charts <ConfigurationThermistors>`.
    temp_chart_e = HT100K3950
    temp_chart_hbp = HT100K3950

    # Extruder maximum temp. 250.0 is a safe number if you are only printing PLA.
    # ABS and PETG will need a higher limit set here (such as 280.0)
    max_temp_E = 280.0 

Endstops
~~~~~~~~

::

    invert_x1 = True # True means endstop is connected as Normally Open (NO) or not connected
    invert_y2 = True # False means endstop is connected as Normally Closed (NC) 
    invert_z1 = True # You can check these with M119 in the OctoPrint terminal
    invert_x2 = True
    invert_y1 = True
    invert_z2 = True
    # If one endstop is hit, which steppers and directions are masked. In other words, what directions should the stepper NOT be allowed to turn
    #   The list is comma separated and has format
    #     x_cw = stepper x clockwise (independent of direction_x)
    #     x_ccw = stepper x counter clockwise (independent of direction_x)
    #   This *is* affected by the direction_* option above.
    #
    #   Steppers e and h (and a, b, c for reach) can also be masked.
    #
    #   For a list of steppers to stop, use this format: x_cw, y_ccw
    #   For CoreXY and similar, two steppers should be stopped if an end stop is hit.
    #     similarly for a delta probe should stop x, y and z.
    end_stop_x1_stops = x_cw,y_cw #This stops the X and Y motors from turning clockwise when the X1 stop is hit (X_Minimum in this example)
    end_stop_y2_stops = x_ccw,y_cw #This stops the X motor from turning CCW and the Y motor from turning CW 
                                  #(Y_Maximum is the location of the limit switch)
    end_stop_z1_stops = z_cw,h_cw #This stops the Z and H motors from turning CW when the Z_Minimum limit switch is hit 
                                   #(H is mirrored to Z, so we have to include it here Otherwise, Z would stop turning, but H 
                                   #would continue to turn

Planner
~~~~~~~

::

    # Max speed for the steppers in meters/sec
    max_speed_x = 0.3 #This sets the maximum speed to 300mm/sec for X
    max_speed_y = 0.3 #300mm/sec for Y
    max_speed_z = 0.3 #300mm/sec for Z
    max_speed_e = 0.2 #200mm/sec for the extruder
    max_speed_h = 0.3 #300mm/sec for H, which is slaved to Z (above)

    # Maximum acceleration in meters/sec
    acceleration_x = 1.5 #1500mm/sec acceleration
    acceleration_y = 1.5
    acceleration_z = 0.5 #500mm/sec acceleration
    acceleration_e = 1.5
    acceleration_h = 0.5

Homing
~~~~~~

::

    #Homing speed in meters/sec
    home_speed_x = 0.05 #Homing for X is be 50mm/sec. It is set to a positive value, as it is homing to X_Minimum
    home_speed_y = -0.05 #Homing for Y is 50mm/sec. It is set to a negative value, as it needs to home to Y_Maximum
    home_speed_z = 0.01 #Home for Z is 10mm/sec
    home_speed_e = 0.01
    home_speed_h = 0.01

Cold-ends
~~~~~~~~~

::

    connect-therm-E-fan-1 = True #Connects the thermistor on the extruder to control the fan plugged into Fan1. In this instance, that is the hot-end cooling fan (not the part fan)
    therm-e-fan-1-target_temp = 50 #Default temperature is 60C. This will change that to 50C. 
    add-fan-0-to-m106=true #I have the part cooling fan plugged into Fan0. This line tells Redeem to use Fan0 when the GCode tells it to turn on the part fan

Fans
~~~~

::
    # 0 is off, 1 is on
    default-fan-0-value = 0.0
    default-fan-1-value = 0.0
    default-fan-2-value = 0.0
    default-fan-3-value = 1.0 #I have a fan plugged into Fan3 to cool the Replicape itself. This line turns the fan on.
