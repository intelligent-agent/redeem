Redeem
======

..  figure:: ./images/redeem_header.png
    :figclass: inline


..  contents:: Table of Contents
    :depth: 3
    :local:

Redeem is the Replicape daemon. It chews G-codes and spits out
coordinates. The software can be found in the redeem repository:
https://bitbucket.org/intelligentagent/redeem

Installation
------------

Debian
~~~~~~

There is now a Debian Jessie package available. Please see :ref:`ManualInstallationOfPackageFeed`
for instructions on adding the feed manually, if you are not using the
preferred distro which is Kamikaze.

Rules
-----

-  All units are in SI-units internally in Redeem, but g-codes often expose mm etc.
-  ``default.cfg`` is the bible, all configs must be defined in there.
-  All configurations in default.cfg can be overridden
-  default.cfg and printer.cfg can be changed with updates. ``local.cfg`` can not.
-  Here is the config hierarchy: ``local.cfg`` > ``printer.cfg`` > ``deafult.cfg``

Overview
--------

Most of redeem is written in Python, but if you look at a typical
G-code file you will see that most of it is G0/G1 codes, so that part
has been optimized. That way you can have seldom used routines like
homing and bed leveling done in a python with all it's garbage garbage
collection and libraries, and just a small part done in C.

..  figure:: ./images/redeem_stack.png
    :figclass: inline



Configuration
-------------

For Redeem, the preferred way to handle configuration is through the web
interface. The web interface is available through
`kamikaze.local <http://kamikaze.local>`__ assuming you have your BeagleBone on the
local network and you are using :doc:`/kamikaze`.

The config files for redeem are present in the folder ``/etc/redeem/``.
There are three files for setting the configuration. ``default.cfg`` is the
catch-all at the bottom. It will contain all the possible options and
**should not be touched**. Second is ``printer.cfg`` which is a symlink and
specific to a printer. Look in the folder to find one that matches your
printer. If you cannot find one, make it! *Otherwise leave the existing
one as is.* Finally is local.cfg which contains quirks or other
individual settings. The ``local.cfg`` will not be overwritten by new
software updates and can contain stuff like microstepping, stepper
current, offsets as well as any bed compensation matrices etc.

Now normally all settings can come from your specific ``printer.cfg`` config
file, but if no one has made that file, you need to set this stuff up
yourself. Most of the stuff in the config files is in SI units. This is
perhaps different than what other firmwares do, where the focus is on
optimization rather than ease of use. Note that it is important to keep
the section headers in the same case as the examples or ``default.cfg`` as
they are case sensitive.

..  important::

    If you edit a config file incorrectly, redeem will fail to load and
    you will be unable to connect in octoprint. You must use headers, as
    shown in the examples, and consistent spacing/formatting. Also the first
    time you load octoprint you will not have any config files listed in
    settings/redeem, you are supposed to load a blank local.cfg file. You
    shouldn't need to do this again unless you reflash the image. However,
    if you find that your config files suddenly when missing, simply close
    your browser tab and reopen octoprint and they should return.

..  note::

    If you are not writing your own new ``printer.cfg``, keep all your printer
    settings in ``local.cfg`` to avoid getting any setting over-written by a redeem update.

There are some comments for the different config variables, but here is
a more detailed explanation on some of them:

System
~~~~~~

The system section has only Replicape board revision and log level. For
debugging purposes, set the log level to 10, but keep it at 20 for
normal operations, since logging is very CPU intensive and can cause
delays during prints at high speed. On later versions of Redeem, the
board revision is read from the EEPROM on the Replicape.

::

    [System]

    # CRITICAL=50, # ERROR=40, # WARNING=30,  INFO=20,  DEBUG=10, NOTSET=0
    loglevel =  20

    # If set to True, also log to file.
    log_to_file = True

    # Default file to log to, this can be viewed from octoprint
    logfile = /home/octo/.octoprint/logs/plugin_redeem.log

    # Plugin to load for redeem, comma separated (i.e. HPX2Max,plugin2,plugin3)
    plugins =

    # Machine type is used by M115
    # to identify the machine connected.
    machine_type = Unknown

Plugins
^^^^^^^

Right now, there are only a few working plugins.

-  HPX2Max: Dual extrusion with the HPX2Max extruder.
-  DualServo: A more general dual extrusion using a servo for switching
   between hot ends.

DualServoPlugin, example config:

::

    [DualServoPlugin]
    # The pin name of where the servo is located
    servo_channel = P9_14
    # minimum pulse length
    pulse_min = 0.01
    pulse_max = 0.02
    angle_min = 0
    angle_max = 180
    extruder_0_angle = 87.5
    extruder_1_angle = 92.5


    [HPX2MaxPlugin]
    # The channel on which the servo is connected. The numbering correspond to the Fan number
    servo_channel = P9_14
    # Extruder 0 angle to set the servo when extruder 0 is selected, in degree
    extruder_0_angle = 20

    # Extruder 1 angle to set the servo when extruder 1 is selected, in degree
    extruder_1_angle = 175

.. _ConfigGeometry:

Geometry
~~~~~~~~

The geometry section contains stuff about the physical layout of your
printer. What the print volume is, what the offset from the end stops
is, whether it's a Normal XY style printer, a Delta printer, an H-belt
type printer or a CoreXY type printer.

It also contains the bed compensation matrix. The bed compensation
matrix is used for compensating any rotation the bed has in relation
to the nozzle. This is typically not something you write yourself, but
instead it is found by probing the bed at different locations by use
of the G-code G29. The G29 command is a macro command, so it only runs
other G-codes and you can override it yourself in the local.cfg file
or in the printer.cfg file if you are a printer manufacturer.


Note on homing
^^^^^^^^^^^^^^

travel\_\*, offset\_\*, and home\_\* (not in this section, see the
`#Homing <#Homing>`__ section) all make up how a homing routine works.
They can all be positive or negative. Here is a quick run-down of what
is happening internally:

#. Travel the distance and direction set in travel\_\*. If an end stop
   is found, stop.
#. Move away the distance found in backoff\_distance\_\*, then hit the
   end stop once more, slower.
#. Move the distance set in offset\_\*, opposite of travel\_\*. The
   offset\_\* sign is thus typically the same as the travel\_\* sign.
#. If the values in home\_\* is 0, the routine is done and the position
   is 0, 0, 0.
#. If there are values in home\_\*, use those values in the G92 command,
   so that the printer will then move to that point, changing the
   position.


Offset\_\* does homing in Cartesian space, so for a delta, the values,
typically have to be the same if you want the nozzle to end up in the
centre, right above the platform. After completing the offset\_\*, a
G92 is issued \_with\_ the values in home\_\* as arguments. If
home\_\* is 0, the homing routine is done, but if there are some
values in home\_\*, the head will move to those positions. the values
in home\_\* are in the native coordinate system, IE delta coordinates
for a delta printer. As a starting point, have home\_\* values = 0,
set the travel\_\* to a small value and offset\_\* to an even smaller
value. That way you can do some testing without ramming your nozzle
into the bed.

::

    [Geometry]
    # 0 - Cartesian
    # 1 - H-belt
    # 2 - Core XY
    # 3 - Delta
    axis_config = 0

    # The total length each axis can travel
    #   This affects the homing endstop searching length.
    #   travel_* can be left undefined.
    #   It will be determined by soft_end_stop_min/max_*
    # travel_x = 0.2
    # ...

    # Define the origin in relation to the endstops
    #   offset_* can be left undefined.
    #   It will be determined by home_speed and soft_end_stop_min/max_*
    # offset_x = 0.0
    # ...

    # The identity matrix is the default
    bed_compensation_matrix =
            1.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, 0.0, 1.0

Delta
~~~~~

Delta support in Redeem is now pretty stable. variables needed for
defining the geometry of the delta setup. If your printer is not a
Delta printer, leave this. Effector is the thing that is in the centre
and moves. The one with the hot end.

- The distance from the centre of the effector to where the rods are
  mounted is the effector offset.

- Carriage is those that move up and down along the columns.

- I've not figured out what the carriage offset does. You should think
  this was the offset from the carriages to the rods, but I've not
  gotten that top work. Seems broken. Instead, add the carriage offset
  to the effector offset.

calibrating convex/concave behaviour
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If your delta printer is exhibiting non-planar behaviour, you can use
:ref:`m665` to calibrate the values. When you have found the correct values, save
them with :ref:`m500`.

The saved settings will be in `local.cfg`.

To see which parameter to change in which direction, looking at this
page will guide you in which value to tune which way: `Delta Calibration Study <http://boim.com/DeltaUtil/CalDoc/Calibration.html>`__

To summarize, set your rod length **L** according to what you have
measured, from center to center of the ball joints. Then adjust the
behavior by adjusting the **R** parameter.

Use a thickness gauge (can be anything that doesn't compress) of a few
millimeters thickness as a reference. First set the Z-height properly
for X,Y = (0,0). Then move 10, 20 millimeters in X and Y around the
center to see if you have a significant error in the planar behavior.
If you don't, move out further and check with your thickness gauge how
far off you are. A quick example of the order of magnitudes is if you
notice a 1 to 1.5mm offset (*upwards means you need to shrink R, too
far down means you need to increase R*) at 40mm off center out of a
3mm gauge. The error in radius was somewhere on the order of 2 or 3mm
to adjust it. The further out from the center, the smaller the
adjustment to be made to the radius.

..  note::

    while the radial offset values exist, `it has been reported`__
    that at present they do not behave as expected. The suggested fix is
    to subtract the offsets directly into your print radius value to get a
    better behavior. This note will be removed when the release branch of
    redeem has corrected the behavior.

__ https://plus.google.com/100077479073911242630/posts/C2dubTjDeMG


bed leveling compensation matrix
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Redeem supports autoprobing the bed
  to generate a bed leveling compensation matrix. However it is no
  substitute for a poorly setup machine. Try to get your head as level
  as possible without bed leveling first, then use the :ref:`g29`
  command to generate the fine-tuning bed compensation matrix.

Using G33 for auto-calibration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you have a working G29 probing setup in place, you can improve
several parameters of your delta printer with the G33 command. The
parameters to improve is end stop offsets, delta radius, tower angular
position correction and diagonal rod length.

G33 will use the probe offset in the [Probe] section to adjust the end
stops offsets, so be sure to set this to 0 initially to avoid offset
errors.

The G33 in Redeem is an implementation of the calculations found in this
web site: http://escher3d.com/pages/wizards/wizarddelta.php

::

    [Delta]
    # Distance head extends below the effector.
    Hez = 0.0
    # Length of the rod
    L   = 0.135
    # Radius of the columns (distance from column to the center of the build plate)
    r   = 0.144
    # Effector offset (distance between the joints to the rods to the center of the effector)
    Ae  = 0.026
    Be  = 0.026
    Ce  = 0.026
    # Carriage offset (the distance from the column to the carriage's center of the rods' joints)
    A_radial = 0.0
    B_radial = 0.0
    C_radial = 0.0

    # Compensation for positional error of the columns
    # (For details, read: https://github.com/hercek/Marlin/blob/Marlin_v1/calibration.wxm)
    # Positive values move the tower to the right, in the +X direction, tangent to it's radius
    A_tangential = 0.0
    B_tangential = 0.0
    C_tangential = 0.0

Here is a visual depiction of what the length and radius looks like:

..  image:: ./images/delta_length_and_radius.png


Here is what the Hez looks like:

..  image:: ./images/delta_hez.png

Steppers
~~~~~~~~

Ah, Steppers! This section has the stuff you need for the the
steppers, such as the number of steps pr mm for each axis, the stepper
max current, the microstepping, acceleration, max speed, the option to
invert a stepper (so you don't have to rotate the stepper connector),
and finally the decay mode of the current chopping on the motor
drives. The decay mode affects the way the stepper motor controllers
decays the current. Basically slow decay will give more of a hissing
sound while standing still and fast decay will cause the steppers to
be silent when stationary, but loud when stepping. The microstepping\_
settings is (2^x), so microstepping\_x = 2 means 2^2 = 4. 3 is then
2^3 = 8. (One eighth to be precise)

Replicape Rev B
^^^^^^^^^^^^^^^

On Replicape Rev B, there are 8 levels of decay. Please consult the `data sheet for TMC2100`__ on the different options.

__ http://www.trinamic.com/_scripts/download.php?file=_articles%2Fproducts%2Fintegrated-circuits%2Ftmc2100%2F_datasheet%2FTMC2100_datasheet.pdf

Decay
~~~~~

There are three settings that are controlled on the TMC2100 by the decay mode or rather “chopper configuration”: CFG0,
CFG4 and CFG5 in the TMC2100 data sheet.

**CFG0:** Sets chopper off time (Duration of slow decay phase)

| DIS - 140 Tclk (recommended, most universal choice)
| EN - 236 Tclk (medium)

**CFG4:** Sets chopper hysteresis (Tuning of zero crossing precision)

| DIS: (recommended most universal choice): low hysteresis with ≈4% offull scale current.
| EN: high setting with ≈6% of full scale current at sense resistor.


**CFG5:** Sets chopper blank time ( Duration of blanking of switching spike )

| Blank time (in number of clock cycles)
| DIS - 16 (best performance for StealthChop)
| EN - 24 (recommended, most universal choice)
|
| 0 - DIS\_CFG0 \| DIS\_CFG4 \| DIS\_CFG5
| 1 - DIS\_CFG0 \| DIS\_CFG4 \| EN\_CFG5
| 2 - DIS\_CFG0 \| EN\_CFG4 \| DIS\_CFG5
| 3 - DIS\_CFG0 \| EN\_CFG4 \| EN\_CFG5
| 4 - EN\_CFG0 \| DIS\_CFG4 \| DIS\_CFG5
| 5 - EN\_CFG0 \| DIS\_CFG4 \| EN\_CFG5
| 6 - EN\_CFG0 \| EN\_CFG4 \| DIS\_CFG5
| 7 - EN\_CFG0 \| EN\_CFG4 \| EN\_CFG5

Microstepping
^^^^^^^^^^^^^

| 0 - Full step
| 1 - Half step
| 2 - Half step, interpolated to 256
| 3 - Quarter step
| 4 - 16th step
| 5 - Quarter step, interpolated to 256 microsteps
| 6 - 16th step, interpolated to 256 microsteps
| 7 - Quarter step, StealthChop, interpolated to 256 microsteps
| 8 - 16th step, StealthChop, interpolated to 256 microsteps

..  danger::

  **Never run the Replicape with the steppers running above 0.5A without cooling**.
  Never exceed 1.2A of regular use either - the TMC2100 drivers aren't
  rated higher. If you need more current to drive two motors off the
  same stepper, use slave mode with a second driver (usually H). Yes, it
  means splitting off your wiring of the stepper motors you had going to
  a single driver, but it also means you avoid overheating your drivers.

Slave mode
^^^^^^^^^^

If you want to enable slave mode for a stepper driver, meaning it will
mirror the movements of another stepper motor exactly, you need to use
“slave\_y = H” if you want the H-stepper motor to mirror the moves
produced by the Y-stepper motor. Remember to also set the steps\_pr\_mm
to the same value on the the motors mirroring each other, and also the
direction. Most likely you will want the current to be the same as well.

#. Enable the slave stepper driver (in\_use\_h = True)
#. The syntax for selecting which axis is the master and which the slave
   is:
   I want to slave H to Z (H follows everything Z does) then you use
   “slave\_z = H”.
#. If you have any endstops acting on the master axis, then you should
   do the same thing for the slave axis, otherwise it will just keep on
   turning. For example, on a delta with Z1 connected to a bed probe and
   Z2 connected to the tower limit switch: “end\_stop\_Z1\_stops =
   x\_neg, y\_neg, z\_neg, h\_neg” and “end\_stop\_Z2\_stops = z\_pos,
   h\_pos”.


::

    # Stepper e is ext 1, h is ext 2
    [Steppers]
    microstepping_x = 3
    ...

    current_x = 0.5
    ...

    # steps per mm:
    #   Defined how many stepper full steps needed to move 1mm.
    #   Do not factor in microstepping settings.
    #   For example: If the axis will travel 10mm in one revolution and
    #                angle per step in 1.8deg (200step/rev), steps_pr_mm is 20.
    steps_pr_mm_x = 4.0
    ...

    backlash_x = 0.0
    ...

    # Which steppers are enabled
    in_use_x = True
    ...

    # Set to -1 if axis is inverted
    direction_x =  1
    ...

    # Set to True if slow decay mode is needed
    slow_decay_x = 0
    ...

    # A stepper controller can operate in slave mode,
    # meaning that it will mirror the position of the
    # specified stepper. Typically, H will mirror Y or Z,
    # in the case of the former, write this: slave_h = Y.
    slave_x =
    ...

    # Stepper timout
    use_timeout = True
    timeout_seconds = 60

Planner
~~~~~~~

The acceleration profiles are trapezoidal, i.e. constant acceleration.
One will probably see and hear a difference between Replicape/Redeem and
the simpler 8 bit boards since all path segments are cut down to 0.1 mm
on delta printers regardless of speed and there is also a better
granularity on the stepper ticks, so you will never have quantized steps
either. Further more, all calculations are done with floating point
numbers, giving a better precision on calculations compared to 8 bit
microcontrollers.

This section is concerned with how the path planner caches and paces the
path segments before pushing them to the PRU for processing.

::

    [Planner]

    # size of the path planning cache
    move_cache_size = 1024

    # time to wait for buffer to fill, (ms)
    print_move_buffer_wait = 250

    # if total buffered time gets below (min_buffered_move_time) then wait for (print_move_buffer_wait) before moving again, (ms)
    min_buffered_move_time = 100

    # total buffered move time should not exceed this much (ms)
    max_buffered_move_time = 1000

    # max segment length
    max_length = 0.001

    acceleration_x = 0.5
    ...

    max_jerk_x = 0.01
    ...

    # Max speed for the steppers in m/s
    max_speed_x = 0.2
    ...

    # Max speed for the steppers in m/s
    min_speed_x = 0.005
    ...

    # When true, movements on the E axis (eg, G1, G92) will apply
    # to the active tool (similar to other firmwares).  When false,
    # such movements will only apply to the E axis.
    e_axis_active = True

Cold ends
~~~~~~~~~

Replicape has three thermistor inputs and a Dallas one-wire input.
Typically, the thermistor inputs are for high temperatures such as hot
ends and heated beds, and the Dallas one-wire input is used for
monitoring the cold end of a hot end, if you know what I mean... This
section is used to connect a fan to one of the temperature probes, so
for instance the fan on your extruder will start as soon as the
temperature goes above 60 degrees. If you have a Dallas one-wire
temperature probe connected on the board, it will show up as a file-like
device in Linux under /sys/bus/w1/devices/. Find out the full path and
place that in your local.cfg. All Dallas one-wire devices have a unique
code, so yours will be different than what you see here.

::

    [Cold-ends]
    # To use the DS18B20 temp sensors, connect them like this.
    # Enable by setting to True
    connect-ds18b20-0-fan-0 = False
    connect-ds18b20-1-fan-0 = False
    connect-ds18b20-0-fan-1 = False

    # This list is for connecting thermistors to fans,
    # so they are controlled automatically when reaching 60 degrees.
    connect-therm-E-fan-0 = False
    ...
    connect-therm-H-fan-1 = False
    ...

    add-fan-0-to-M106 = False
    ...

    # If you want coolers to
    # have a different 'keep' temp, list it here.
    cooler_0_target_temp = 60

    # If you want the fan-thermistor connections to have a
    # different temperature:
    # therm-e-fan-0-target_temp = 70

Heaters
~~~~~~~

The heater section controls the PID settings and which temperature
lookup chart to use for the thermistor. If you do not find your
thermistor in the chart, you can find the Steinhart-Hart coefficients
from the `NTC Calculator`__ online tool.

__ http://www.thinksrs.com/downloads/programs/Therm%20Calc/NTCCalibrator/NTCcalculator.htm

Some of the most common thermistor coefficients have already been
implemented though, so you might find it here:


Steinhart-Heart Thermistors
^^^^^^^^^^^^^^^^^^^^^^^^^^^

+--------------------+-------------------------------------------------------------------+
| Name               | Comment                                                           |
+====================+===================================================================+
| B57540G0104F000    | EPCOS100K with b= 4066K                                           |
+--------------------+-------------------------------------------------------------------+
| B57560G1104F       | EPCOS100K with b = 4092K                                          |
+--------------------+-------------------------------------------------------------------+
| B57560G104F        | EPCOS100K with b = 4092K (Hexagon)                                |
+--------------------+-------------------------------------------------------------------+
| B57561G0103F000    | EPCOS10K                                                          |
+--------------------+-------------------------------------------------------------------+
| NTCS0603E3104FXT   | Vishay100K                                                        |
+--------------------+-------------------------------------------------------------------+
| 135-104LAG-J01     | Honeywell100K                                                     |
+--------------------+-------------------------------------------------------------------+
| SEMITEC-104GT-2    | Semitec (E3D V6)                                                  |
+--------------------+-------------------------------------------------------------------+
| DYZE               | DYZE hightemp thermistor                                          |
+--------------------+-------------------------------------------------------------------+
| HT100K3950         | RobotDigg.com's 3950-100K thermistor (part number HT100K3950-1)   |
+--------------------+-------------------------------------------------------------------+


PT100 type thermistors
^^^^^^^^^^^^^^^^^^^^^^

+--------------------------+-----------------------------+
| Name                     | Comment                     |
+==========================+=============================+
| E3D-PT100-AMPLIFIER      | E3D PT100                   |
+--------------------------+-----------------------------+
| PT100-GENERIC-PLATINUM   | Ultimaker heated bed etc.   |
+--------------------------+-----------------------------+


Linear v/deg Scale Thermocouple Boards
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

+----------+-------------------------+
| Name     | Comment                 |
+==========+=========================+
| Tboard   | 0.005 Volts pr degree   |
+----------+-------------------------+


Config section
~~~~~~~~~~~~~~~~

Below is what the configuration for the E looks like. The most
important thing to change should be the sensor name matching the
thermistor. The Kp, Ti and Td values will be set by the M303 auto-tune
and the rest of the values are for advanced tuning or special cases.

::

    [Heaters]
    sensor_E = B57560G104F
    pid_Kp_E = 0.1
    pid_Ti_E = 100.0
    pid_Td_E = 0.3
    ok_range_E = 4.0
    max_rise_temp_E = 10.0
    max_fall_temp_E = 10.0
    min_temp_E = 20.0
    max_temp_E = 250.0
    path_adc_E = /sys/bus/iio/devices/iio:device0/in_voltage4_raw
    mosfet_E = 5
    onoff_E = False
    prefix_E = T0
    max_power_E = 1.0

    ...

PID autotune
^^^^^^^^^^^^

With version 1.2.6 and beyond, the PID autotune algorithm is fairly
stable. To run an auto-tune, use the M-code M303. You should see the
hot-end or heated bed temperature oscillate for a few cycles before
completing. To set temperature, number of oscillations, which hot end to
calibrate etc, try running “M303?” or see the description of the :ref:`M303`.

Endstops
~~~~~~~~

Use this section to specify whether or not you have end stops on the
different axes and how the end stop inputs on the board interacts with
the steppers. The lookup mask is useful for the latter. In the default
setup, the connector marked X1 is connected to the stepper on the
X-axis. For CoreXY and H-bot this is different in that two steppers are
denied movement in one direction, but allowed movement in the other
direction given that one of the end stops has been hit.

Also of interest is the use of two different inputs for a single axis
and direction. Imagine using one input to control the lower end of the
Z-axis and a different input to probe the bed with G20/G30.

If you are not seeing any movement even though no end stop has been hit,
try inverting the end stop.

See also this `blog post and video`__ for a more thorough explanation.

__ http://www.thing-printer.com/end-stop-configuration-for-redeem/

Soft end stops
^^^^^^^^^^^^^^

Soft end stops can be used to prevent the print head from moving beyond
a specified point. For delta printers this is useful since they cannot
have end stops preventing movement outside the build area.

::

    [Endstops]
    # Which axis should be homed.
    has_x = True
    ...
    # Number of cycles to wait between checking
    # end stops. CPU frequency is 200 MHz
    end_stop_delay_cycles = 1000

    # Invert =
    #   True means endstop is connected as Normally Open (NO) or not connected
    #   False means endstop is connected as Normally Closed (NC)
    invert_X1 = False
    ...
    # If one endstop is hit, which steppers and directions are masked.
    #   The list is comma separated and has format
    #     x_cw = stepper x clockwise (independent of direction_x)
    #     x_ccw = stepper x counter clockwise (independent of direction_x)
    #     x_neg = stepper x negative direction (affected by direction_x)
    #     x_pos = stepper x positive direction (affected by direction_x)
    #   Steppers e and h (and a, b, c for reach) can also be masked.
    #
    #   For a list of steppers to stop, use this format: x_cw, y_ccw
    #   For Simple XYZ bot, the usual practice would be
    #     end_stop_X1_stops = x_neg, end_stop_X2_stops = x_pos, ...
    #   For CoreXY and similar, two steppers should be stopped if an end stop is hit.
    #     similarly for a delta probe should stop x, y and z.
    end_stop_X1_stops =
    ...
    soft_end_stop_min_x = -0.5
    ...
    soft_end_stop_max_x = 0.5
    ...

Endstop troubleshooting advice
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This was a short troubleshooting advice provided on Slack - it's being
pasted here as-is until it can be rephrased and re-worked into the
documentation properly:

Redeem basic endstop config! First and foremost make sure your endstops
are working before trying to move. Now in redeem that is not quite as
simple as you would expect. For these instructions make sure your bed is
somewhere near the middle of its travel we do not want anything crashing
into anything!

Go to your terminal in Octoprint and press your enstops with your finger
one at a time you should get a response saying enstop # hit (# being
what axis you just triggered) If you do not get a response Stop do not
go further until you do get a resposnse!

Next go to your controls in octoprint and select 1mm and for Z press the
UP arrow it should move 1mm away from bed for some printers with fixed
beds that means usually the nozzle moves up! On others that have a bed
that moves away from the nozzle because the nozzle is fixed in the Z
plane it means the bed moves down!

We will stay with the Z axis now press the Z endstop and again try to
move 1mm UP ( UP Arrow) if it does not move try moving the Z with the
Down button it should move one or the other way this with tell you which
way you have the endstop stopping movement.

For your particular printer and endstop location you need to edit the
end\_stop\_Z1\_stops = z\_cw #stopping direction in a clockwise
direction (I think you can use pos or neg as well) end\_stop\_Z1\_stops
= z\_ccw #stopping direction in a counter clockwise

Soft Enstops You must have these set to outside your full travel in the
min and the max soft\_end\_stop\_min\_z = -0.30 #300mm set to your
printer travel plus some extra soft\_end\_stop\_max\_z = 0.30 #300mm you
can configure to suit your requirements after! these settings are in
METERS

If these are set wrong you will not move as expected you will not probe
as expected!!!!

If you need to change direction of motors this is the line 1 or -1
direction\_z = -1

The other Axis will be a similar procedure.

Homing
~~~~~~

This section has to do with the speed of the homing and how much the
stepper should back away for each axis to do fine search. Please note
that there are two other variables in :ref:`ConfigGeometry` section
that are related to the homing routine: travel_* and offset_*. The
offset_* values will move the print head immediately after homing,
while the home_* settings found in this section can be used to set an
offset to delta printers, so the head is kept by the end stops.

::

    [Homing]

    # Homing speed for the steppers in m/s
    #   Search to minimum ends by default. Negative value for searching to maximum ends.
    home_speed_x = 0.1

    # homing backoff speed
    home_backoff_speed_x = 0.01

    # homing backoff dist
    home_backoff_offset_x = 0.01

    # Where should the printer goes after homing
    #   home_* can be left undefined. It will stay at the end stop.
    # home_x = 0.0
    # ...

Multi-extrusion
~~~~~~~~~~~~~~~

Currently Redeem does not yet support tool offsets for dual or
multi-extrusion. These offsets must be configured in the slicer, instead
of in the firmware, for now.

Servos
~~~~~~

Rev A
^^^^^

You can control servos through Redeem and the way you do it is by using
one of the left over channels on the PWM chip. A total of six channels
are broken out through the expansion header named expand on Replicape
A4A. Here is a list of the pins and which channel it is connected to:

-  Pin 9 -> Channel 14
-  Pin 8 -> Channel 15
-  Pin 7 -> Channel 7
-  Pin 5 -> Channel 11
-  Pin 3 -> Channel 12
-  Pin 1 -> Channel 13

The control signal is 3.3 V square waves which will probably not be
sufficient to power larger servos without a level shifter, but some
miniature servos can both be operated and powered with 3.3 V.

Rev B
^^^^^

Servos are controlled by two on-chip PWMs and share connector with
Endstop X2 and Y2.

-  Servo 0 is on pin P9\_14
-  Servo 1 is on pin P9\_16

Use :ref:`m280` to set
the servo position. Note that multiple servos can be present, the init
script will continue to initialize servos as long as there are higher
indexes, so keep the indexes increasing for multiple servos.

::

    [Servos]
    # For Rev B, servo is either P9_14 or P9_16.
    # Not enabled for now, just kept here for reference.
    # Angle init is the angle the servo is set to when redeem starts.
    # pulse min and max is the pulse with for min and max position, as always in SI unit Seconds.
    # So 0.001 is 1 ms.
    # Angle min and max is what angles those pulses correspond to.
    servo_0_enable = False
    servo_0_channel = P9_14
    servo_0_angle_init = 90
    servo_0_angle_min = -90
    servo_0_angle_max = 90
    servo_0_pulse_min = 0.001
    servo_0_pulse_max = 0.002

Z-Probe
~~~~~~~

Before attempting the configuration of a Z probe make sure your printer
is moving in the right direction and that your hard endstops and your
soft endstops are configured correctly please refer to the endstop
section.

| The standard configs for Z-probe should work for most. The real
  difficulty lies in making the macro for the whole probing procedure.
  The offsets are the distance from the probe point to the nozzle. Here
  are the standard values:

::

    [Probe]
    length = 0.01
    speed = 0.05
    accel = 0.1
    offset_x = 0.0
    offset_y = 0.0

Hitwall's advice from slack
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Z Probes are a great addition to the 3d printer! Having said that they
do not take the place of careful initial manual config. For Delta
printers they can be helpful for the calibration procedure but again
they will not solve a badly built printer. I would suggest you should
have your printer in a basic configured state.

First steps For a circular bed use : G29C #to create a macro for you(
look at the wiki for details on it usage) M500 # to save to your
local.cfg

For a rectangle bed use G29S # to create a macro for you( look at the
wiki for details on it usage) M500 # to save to your local.cfg

Edit the local.cfg and add the appropriate G31 and G32 Macro.

::

    G32       some Macro examples:

    G32 =
         M106 P2 S255                    ; Turn on power to probe.
    G32 =
         M574 Z2 x_ccw,y_ccw,z_ccw    ; enable Z2 endstop
    G32 =
        M280 P0 S-60 F3000              ; Probe down (Undock sled)

    G31       some Macro examples:

    G31 =
         M106 P2 S0                        ; Turn off power to probe.
    G31=
         M574 Z2                         ; disable Z2 endstop
    G31 =
        M280 P0 S320 F3000              ; Probe up (dock sled)

The same procedure as endstops First make sure your Z probe triggers the
endstop Next make sure the Z probe stops motion (refer to endstop
section for more detail.) Set your Z probe travel speed ...slow it down
until your sure it works correctly. Test and happy probing!

Rotary-encoders
~~~~~~~~~~~~~~~

..  warning::

    work in progress. See the blog post `Filament Sensor <http://www.thing-printer.com/filament-sensor-3d-printer-replicape/>`_.

::

    [Rotary-encoders]
    enable-e = False
    event-e = /dev/input/event1
    cpr-e = -360
    diameter-e = 0.003

Filament-Sensors
~~~~~~~~~~~~~~~~

.. warning::

    work in progress.

::

    [Filament-sensors]
    # If the error is > 1 cm, sound the alarm
    alarm-level-e = 0.01

Watchdog
~~~~~~~~

The watchdog is a time-out alarm that will kick in if the
/dev/watchdog file is not written at least once pr. minute. This is a
safety issue that will cause the BeagleBone to issue a hard reset if
the Redeem daemon were to enter a faulty state and not be able to
regulate the heater elements. For the watchdog to start, it requires
the watchdog to be resettable, with the proper kernel command line ``omap\_wdt.nowayout=0``.

This should be left on at all time as a safety precauchion, but can be
disabled for development purposes. This is not the same as the stepper
watchdog which only disables the steppers.

::

    [Watchdog]
    enable_watchdog = True

Macros
~~~~~~

The macro-section contains macros. Duh. Right now, only G29, G31 and G32
has macro definitions and it's basically a set of other G-codes. To make
a new macro, you need to also define the actual g-code file for it. That
is beyond this wiki, but look at G29 in the repository, for instance:
`2 <https://bitbucket.org/intelligentagent/redeem/src/73c21486b1e294570a125e9fac6c9cef9b4f273b/redeem/gcodes/G29.py?at=develop>`__

..  note::

    Each line in macros section needs to be spaced the same or you may
    not be able to connect in octoprint. Most Inductive sensors don't need
    probe type defined to work. To simply turn an inductive sensor on and
    off change the example macro with the g31/g32 macro's i have listed
    here. The g32 may need adjusting to match your z1 endstop settings.
    Undock turns probe on, Dock turns it off. Check your Macro and setup
    carefully, in the g29 example, at the end of each probe point it docks
    your probe then homes z before the start of the next point, which in
    some printers can crash your probe into the bed possibly causing damage.

If you find that your probe routine is probing the air, your z
axis is most likely moving in the wrong direction for the probing
to work. It seems redeem only probes in one direction and this
can't be changed in the probing settings. So, You will need to
swap your z direction, in the [steppers] section using
direction\_z = -1 or direction\_z = +1, then confirm your z
stops/homing, ect work make corrections as required. You will also
most likely need to change under [Geometry] travel\_z direction.
This should trick the probe into moving in the correct direction.

**G31**::

    M574 Z2  ; Probe up (Dock sled)

**G32**::

    M574 Z2 z_ccw, h_ccw  ; Probe down (Undock sled)

::

    [Macros]
    G29 =
        M561                ; Reset the bed level matrix
        M558 P0             ; Set probe type to Servo with switch
        M557 P0 X10 Y20     ; Set probe point 0
        M557 P1 X10 Y180    ; Set probe point 1
        M557 P2 X180 Y100   ; Set probe point 2
        G28 X0 Y0           ; Home X Y

        G28 Z0              ; Home Z
        G0 Z12              ; Move Z up to allow space for probe
        G32                 ; Undock probe
        G92 Z0              ; Reset Z height to 0
        G30 P0 S            ; Probe point 0
        G0 Z0               ; Move the Z up
        G31                 ; Dock probe

        G28 Z0              ; Home Z
        G0 Z12              ; Move Z up to allow space for probe
        G32                 ; Undock probe
        G92 Z0              ; Reset Z height to 0
        G30 P1 S            ; Probe point 1
        G0 Z0               ; Move the Z up
        G31                 ; Dock probe

        G28 Z0              ; Home Z
        G0 Z12              ; Move Z up to allow space for probe
        G32                 ; Undock probe
        G92 Z0              ; Reset Z height to 0
        G30 P2 S            ; Probe point 2
        G0 Z0               ; Move the Z up
        G31                 ; Dock probe

        G28 X0 Y0           ; Home X Y

        M561 U; (RFS) Update the matrix based on probe data
        M561 S; Show the current matrix
        M500; (RFS) Save data


    G31 =
        M280 P0 S320 F3000  ; Probe up (Dock sled)

    G32 =
        M280 P0 S-60 F3000  ; Probe down (Undock sled)



..  important::

    There is a configuration page where you can choose what ``printer.cfg`` links to and edit ``local.cfg``.

Implemented Gcodes
------------------

You can always get the updated list of implemented gcodes by writing “G”
or “M” in the terminal on Octoprint. For a longer description of each
gcode write the code + “?” in the terminal. So to get a description of
G1, write::

    G1?

The list on the reprap wiki has been used a starting point for the
implementation, but some codes, such as stepper decay etc. has been
added separately. Some G-codes have not been implemented, specifically
those related to SD card uploads etc. They are for old fashioned
controller boards, and do not apply to a 4 GB MMC drive.

G: List of currently implemented G-codes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This list has been autogenerated by issuing 'G F0' in Redeem

G: List all implemented G-codes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Lists all the G-codes implemented by this firmware. To get a long
description of each code use '?' after the code name, for instance, G0?
will give a long description of G0

G0: Control the printer head position as well as the currently selected tool
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

| Move each axis by the amount and direction depicted.
| X = X-axis (mm)
| Y = Y-axis (mm)
| Z = Z-axis (mm)
| E = E-axis (mm)
| H = H-axis (mm)
| A = A-axis (mm) - only if axis present
| B = B-axis (mm) - only if axis present
| C = C-axis (mm) - only if axis present
| F = move speed (mm/min) - stored until daemon reset
| Q = move acceleration (mm/min^2) - stored until daemon reset


G1: Control the printer head position as well as the currently selected tool
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Move each axis by the amount and direction depicted.
| X = X-axis (mm)
| Y = Y-axis (mm)
| Z = Z-axis (mm)
| E = E-axis (mm)
| H = H-axis (mm)
| A = A-axis (mm) - only if axis present
| B = B-axis (mm) - only if axis present
| C = C-axis (mm) - only if axis present
| F = move speed (mm/min) - stored until daemon reset
| Q = move acceleration (mm/min^2) - stored until daemon reset


G2: Clockwise arc
^^^^^^^^^^^^^^^^^

Clockwise arc

G3: Counter-clockwise arc
^^^^^^^^^^^^^^^^^^^^^^^^^

Counter-clockwise arc

G21: Set units to millimeters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set units to millimeters

G28: Move the steppers to their homing position (and find it as well)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Move the steppers to their homing position. The printer will travel a
maximum length and directiondefined by travel\_\*. Delta printers will
home both X, Y and Z regardless of whicho of those axes were specified
to home.For other printers, one or more axes can be specified. An axis
will only be homed if homing of that axis is enabled.

..  _g29:


G29: Probe the bed at specified points
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Probe the bed at specified points and update the bed compensation matrix
based on the found points. Add 'S' to NOT update the bed matrix.

G29C: Generate a circular probe pattern
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

| Generate a circular G29 Probing pattern
| D = bed\_diameter\_mm, default: 140
| C = Circles, default = 2
| P = points\_pr\_circle, default: 8
| S = probe\_start\_height, default: 6.0
| Z = add\_zero, default = 1
| K = probe\_speed, default: 3000.0


G29S: Generate a square probe pattern for G29
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Generate a square G29 Probing pattern

| W = bed depth mm, default: 200.0
| D = bed depth mm, default: 200.0
| P = points in total, default: 16
| S = probe start height, default: 6.0
| K = probe\_speed, default: 3000.0


G30: Probe the bed at current point
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Probe the bed at the current position, or if specified, a
pointpreviously set by M557. X, Y, and Z starting probe positions can
be overridden, D sets the probe length, or taken from config if
nothing is specified.

| F sets the probe speed. If not present, it's taken from the config.
| A sets the probe acceleration. If not present, it's taken from the
  config.
| B determines if the bed marix is used or not. (0 or 1)
| P the point at which to probe, previously set by M557.
| P and S save the probed bed distance to a list that corresponds with
  point P

G31: Dock sled
^^^^^^^^^^^^^^

Dock sled. This is a macro G-code, so it will read all gcodes that has
been defined for it. It is intended to remove or disable the Z-probing
mechanism, either by physically removing it as is the case of a servo
controlled device, or by disabling power to a probe or simply disabling
the switch as an end stop

G32: Undock sled
^^^^^^^^^^^^^^^^

Undock sled

G33: Autocalibrate a delta printer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Do delta printer autocalibration by probing the points defined in
the G29 macro and then performing a linear least squares optimization
to minimize the regression residuals.

Fn Number of factors to optimize, parameters::

    3 factors (endstop corrections only)
    4 factors (endstop corrections and delta radius)
    6 factors (endstop corrections, delta radius, and two tower angular position corrections)
    7 factors (endstop corrections, delta radius, two tower angular position corrections, and diagonal rod length)

::

    S Do NOT update the printer configuration.
    P Print the calculated variables

G34: Measure probe tip Z offset (height distance from print head)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Measure the probe tip Z offset, i.e., the height difference of probe
tip and the print head. Once the print head is moved to touch the bed,
this command lifts the head for Z mm, runs the G32 macro to deploy the probe, and
then probes down until the endstop is triggered. The height difference
is then stored as the [Probe] offset\_z configuration parameter.

Parameters:

====== ====================================================
``Df`` Probe move maximum length
``Ff`` Probing speed
``Af`` Probing acceleration
``Zf`` Upward move distance before probing (default: 5 mm)
``S``  Simulate only (do not store the results)
====== ====================================================

G4: Dwell for P (milliseconds) or S (seconds)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Dwell/sleep for a given time. Use either P = milliseconds or S =
seconds.

G90: Set movement mode to absolute
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set movement mode to absolute

G91: Set movement mode to relative
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set movement mode to relative

G92: Set the current position of steppers without moving them
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set the current position of steppers without moving them

M: List of currently implemented M-codes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This list has been autogenerated by issuing 'M F0' in Redeem

M: List all M-codes
^^^^^^^^^^^^^^^^^^^

Lists all the M-codes implemented by this firmware. To get a long
description of each code use '?' after the code name, for instance, M92?
will give a decription of M92. To get all g-codes with wiki formatting,
add token 'F0'.

M101: Deprecated
^^^^^^^^^^^^^^^^

Deprecated

M103: Deprecated
^^^^^^^^^^^^^^^^

Deprecated

M104: Set extruder temperature
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set extruder temperature. Use either T or P to choose heater, use S for
the target temp

M105: Get extruder temperature
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Gets the current extruder temperatures, power and cold end temperatures.
Extruders have prefix T, cold endsa have prefix C, power has prefix @

M106: Set fan power.
^^^^^^^^^^^^^^^^^^^^

Set the current fan power. Specify S parameter for the power (between 0
and 255) and the P parameter for the fan number. P=0 and S=255 by
default. If no P, use fan from config. If no fan configured, use fan 0.
If 'R' is present, ramp to the value

M107: set fan off
^^^^^^^^^^^^^^^^^

Set the current fan off. Specify P parameter for the fan number. If no
P, use fan from config. If no fan configured, use fan 0

M108: Deprecated
^^^^^^^^^^^^^^^^

Deprecated; Use M104 and M140 instead

M109: Set extruder temperature and wait for it to be reached
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set extruder temperature and wait for it to be reached

M110: Set current gcode line number
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set current gcode line number

M111: Set debug level
^^^^^^^^^^^^^^^^^^^^^

set debug level, S sets the level. If no S is present, it is set to 20 =
Info

M112: Cancel all the planned move in emergency.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Cancel all the planned move in emergency.

M114: Get current printer head position
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get current printer head position. The returned value is in meters.

M115: Get Firmware Version and Capabilities
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get Firmware Version and CapabilitiesWill return the version of Redeem
running, the machine type and the extruder count.

M116: Wait for all temperature to be reached
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Wait for all temperature to be reached

M117: Send a message to a connected display
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use 'M117 message' to send a message to a connected display. Typically
this will be a Manga Screen or similar.

M119: Get current endstops state or set invert setting
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get current endstops state. If two tokens are supplied, the first is end
stop, the second is invert state. Ex: M119 X1 1 to invert ends stop X1

M130: Set PID P-value, Format (M130 P0 S8.0)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set PID P-value, Format (M130 P0 S8.0), S<-1, 0, 1>

M131: Set PID I-value, Format (M131 P0 S8.0)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set PID I-value, Format (M131 P0 S8.0)

M132: Set PID D-value, Format (M132 P0 S8.0)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set PID D-value, Format (M132 P0 S8.0)

M140: Set heated bed temperature
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set heated bed temperature

M141: Set fan power and PWM frequency
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set fan power and PWM frequency

M151: Enable min temperature alarm
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Should be enabled after target temperatures have been reached, typically
after an M116 G-code or similar. Once enabled, if the temperature drops
below the set point, the print will stop and all heaters will be
disabled. The min temp will be disabled once a new temperture is set.
Example: M151

M17: Enable steppers
^^^^^^^^^^^^^^^^^^^^

Power on and enable all steppers. Motors are active after this command.

M18: Disable all steppers or set power down
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Disable all steppers. No more current is applied to the stepper motors
after this command. If only token D is supplied, set power down mode (0
or 1)

M19: Reset the stepper controllers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Reset the stepper controllers

M190: Set heated bed temperature and wait for it to be reached
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set heated bed temperature and wait for it to be reached

M201: Set print acceleration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sets the acceleration that axes can do in units/second^2 for print
moves. For consistency with the rest of G Code movement this should be
in units/(minute^2) Example: M201 X1000 Y1000 Z100 E2000

M206: Set or get end stop offsets
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If no parameters are given, get the current end stop offsets.
To set the offset, provide the axes and their offset relative to
the current value. All values are in mm.

Example: ``M206 X0.1 Y-0.05 Z0.03``

M21: Deprecated
^^^^^^^^^^^^^^^

Disabled; Redeem does not have support for SD cards.

M220: Set speed override percentage
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

M220 S - set speed factor override percentage

M221: Set extruder override percentage
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

M221 S - set extrude factor override percentage

M24: Resume the print where it was paused by the M25 command.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Resume the print where it was paused by the M25 command.

M25: Pause the current print.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pause the current print.

M270: Set coordinate system
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set coordinate system. Parameter S set the type, which is 0 = Cartesian,
1 = H-belt, 2 = CoreXY, 3 = Delta

..  _m280:

M280: Set servo position
^^^^^^^^^^^^^^^^^^^^^^^^

Set servo position. Use 'S' to specify angle, use 'P' to specify index,
use F to specify speed.

M301: Set P, I and D values, Format (M301 E0 P0.1 I100.0 D5.0)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set P, I and D values, Format (M301 E0 P0.1 I100.0 D5.0)P = Kp, default
= 0.0I = Ti, default = 0.0D = Td, default = 0.0E = Extruder, -1=Bed,
0=E, 1=H, 2=A, 3=B, 4=C, default = 0

.. _m303:

M303: Run PID tuning
^^^^^^^^^^^^^^^^^^^^

PID Tuning refers to a control algorithm used in some repraps to tune
heating behavior for hot ends and heated beds. This command generates
Proportional (Kp), Integral (Ki), and Derivative (Kd) values for the
hotend or bed (E-1). Send the appropriate code and wait for the output
to update the firmware. E<0 or 1> overrides the extruder. Use E-1 for
heated bed.

=========== ===============================================================
``E``       Extruder with index 0 (default)
``S``       overrides the temperature to calibrate for. Default is 200.
``C``       overrides the number of cycles to run, default is 4
``P (0,1)`` Enable pre-calibration. Useful for systems with very high power
``Q``       Tuning algorithm. 0 = Tyreus-Luyben, 1 = Zieger-Nichols classic
=========== ===============================================================

M308: Set or get direction and search length for end stops
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

| Set or get direction and search length for end stops
| If not tokens are given, return the end stop travel search length in
  mm.
| If tokens are given, they must be a space separated list of pairs.
| Example: 'M308 X250 Y220'. This will set the travel search length for
  the
| X nd Y axis to 250 and 220 mm. Th values will appear in the config
  file in meters, thus 0.25 and 0.22

M31: Set stepper current limit settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set stepper current limit settings

M350: Set microstepping value
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set microstepping mode for the axes present with a token. Microstepping
will be 2^val. Steps pr. mm. is changed accordingly.

M400: Wait until all buffered paths are executed
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Wait until all buffered paths are executed

M409: Get a status report from each filament sensor connected, or enable action command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get a status report from each filament sensor connectedIf the token 'F'
is present, get a human readable status. If no token is present, return
a machine readable form, similar to the return from temperature sensors,
M105. If token 'E' is present without token value, enable sending
filament data for all sensors. If a value is present, enable sending
filament data for this extruder number. Ex: M409 E0 - enables sending
filament data for Extruder 0 (E), M409 E - Enable action command
filament data for all filament sensorsM409 D - Disable sending filament
data for all filament sensors

..  _m500:

M500: Store parameters to file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Save all changed parameters to file.

M557: Set probe point
^^^^^^^^^^^^^^^^^^^^^

Set probe point

M558: Set probe type
^^^^^^^^^^^^^^^^^^^^

Set probe type

M561: Show, update or reset bed level matrix to identity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

| This cancels any bed-plane fitting as the result of probing (or
  anything else) and returns the machine to moving in the user's
  coordinate system.
| Add 'S' to show the marix instead of resetting it.
| Add 'U' to update the current matrix based on probe data

M562: Reset temperature fault.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Reset a temperature fault on heater/sensor If the priner has switched
off and locked a heater because it has detected a fault, this will reset
the fault condition and allow you to use the heater again. Obviously to
be used with caution. If the fault persists it will lock out again after
you have issued this command. P0 is the bed; P1 the first extruder, and
so on.

M569: Set stepper direction
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set the direction for each axis. Use for each of the axes you want.Axis
is one of X, Y, Z, E, H, A, B, C and direction is 1 or -1Note: This will
store the result in the local config and restart the path planner

M574: Set or get end stop config
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If not tokens are given, return the current end stop config. To set the
end stop config: This G-code takes one end stop, and one configuration
where the configuration is which stepper motors to stop and the
direction in which to stop it. Example: M574 X1 x\_ccw This will cause
the X axis to stop moving in the counter clock wise direction. Note that
this recompiles and restarts the firmware

M608: Set stepper slave mode
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

| Set stepper slave mode, making one stepper follow the other.
| If no tokens are given, return the current setup
| For each token, set the second argument as slave to the first
| So M608 XY will set Y as a slave to X
| If only the axis is given, no slave is set.

..  _m665:

M665: Set delta arm calibration values
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

L sets the length of the arm. If the objects printed are too small, try
increasing(?) the length of the armR sets the radius of the towers. If
the measured points are too convex, try increasing the radius

M666: Set axis offset values
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set axis offset values

M668: Adjust backlash compensation for each named axis
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Adjust backlash compensation for each named axis

M81: Shutdown or restart Replicape
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Shutdown the whole Replicape controller board. If paramter P is present,
only exit loop. If R is present, restart daemon

M82: Set the extruder mode to absolute
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Makes the extruder interpret extrusion as absolute positions. This is
the default in Redeem.

M83: Set the extruder mode to relative
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Makes the extruder interpret extrusion values as relative positions.

M84: Set stepper in lowest current mode
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set each of the steppers with a token to the lowest possible current
mode. This is similar to disable, but does not actually disable the
stepper.

M906: Set stepper current in mA
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set the stepper current. Unit is mA. Typical use is 'M906 X400'.This
sets the current to 0.4A on the X stepper motor driver.Can be set for
multiple stepper motor drivers at once.

M907: Set stepper current in A
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set stepper current in A

M909: Set stepper microstepping settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Example: M909 X3 Y5 Z2 E3Set the microstepping value foreach of the
steppers. In Redeem this is implementedas 2^value, so M909 X2 sets
microstepping to 2^2 = 4, M909 Y3 sets microstepping to 2^3 = 8 etc.

M910: Set stepper controller decay mode
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

| Example: M910 X3 Y5 Z2 E3Set the decay mode foreach of the steppers.
  In Redeem this is implementedfor Replicape rev B as a combination of
  CFG0, CFG4, CFG5.A value between 0 and 7 is allowed, setting the three
  registers to the binary value represented by CFG0, CFG4, CFG5.
| CFG0 is chopper off time, the duration of slow decay phase.
| CFG4 is chopper hysteresis, the tuning of zero crossing precision.
| CFG5 is the chopper blank time, the dureation of banking of switching
  spike.
| Please refer to the data sheet for further details on the configs.

M92: Set number of steps per millimeters for each steppers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set number of steps per millimeters for each steppers

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
