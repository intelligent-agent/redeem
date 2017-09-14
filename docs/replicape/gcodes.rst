G-Code Reference
================


..  gcodes::


---------------------------------
















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


.. _mybestgcode:

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

i am referencing it this way :ref:`abc`

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
