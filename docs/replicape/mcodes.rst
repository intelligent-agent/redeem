M-Code Reference
================

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