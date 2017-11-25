Migrate from Marlin
===================

Understanding the difference between Marlin and Redeem
------------------------------------------------------

Redeem is a completely new 3d printer controller. It's been optimized to
run on the BeagleBone Black with a Replicape. It's written in Python
with some parts in C++.

The biggest advantage of Redeem over other embedded programs, is that it
actually runs on linux. It uses the BeagleBone Black's secondary
microcontrollers for real-time operations, but still runs most of the
computations in Linux process space. This makes it more efficient for
complex computation, memory management, etc. that all software engineers
have to face when writing embedded software. Here, it takes advantage of
Linux providing a complete resource management platform (and a good one
at that!) and lets the development focus on what's important for the
features of the software. It also means that, if someone were to develop
an alternative to the BeagleBone which also has dedicated realtime
controllers, Redeem could fully take advantage of it and quite likely of
a stronger processing platform. Python and C++ are easily ported to
other processors, so it's future-proof for any electronic upgrade we'll
see over time.

Hotend settings
~~~~~~~~~~~~~~~

Setting the thermistor type
^^^^^^^^^^^^^^^^^^^^^^^^^^^

One thing that Redeem does a little differently from other firmwares, is
the handling of the thermistors. It relies on having a “chart file”
which is part of the configuration's external files. This means, of
course, that the temperature sensor possibilities are nearly limitless.
You simply need to be able to provide the proper data in a file and pass
it in Redeem's configuration.

Temperature PID settings
^^^^^^^^^^^^^^^^^^^^^^^^

Depending on what your printer type and hotend is, there are a few
defaults to be found in the default configurations provided by Redeem.
However, your setup may vary widely from the stock setup those values
were selected for. So, to select proper PID values, the best is to do
just as you would with another firmware, a calibration phase.

In Redeem, the PID calibration is done using the **M303** command. A
typical example of what you would do (if you print mostly around 210
degrees) is to run **M303 S210 C8** to run 8 cycles of the hotend going
from cold to the target temperature, cooling down and going back up.
This will allow for a good refinement, and it will give you P, I and D
values to put into your local.cfg file in the terminal after the last
cycle completes.

Configuring a printer on Redeem with Marlin values
--------------------------------------------------

Steppers
~~~~~~~~

So. You come from Marlin, and you had your steppers set to, for example,
1/32 microstep, and you have 18-tooth GT-2 pulleys. Your Marlin
configuration looked something like this:

``#define DEFAULT_AXIS_STEPS_PER_UNIT   {200, 200, 200, 900}``

Good! So you know which values you needed for Marlin. Except Marlin
considered a “step” to be every (in this example 1/32nd) microstep, and
it needed 200 microsteps to advance by a millimeter. Redeem doesn't
expect that. In fact, the default.cfg in Redeem shows this comment:

| ``# Defined how many stepper full steps needed to move 1mm.``
| ``#   Do not factor in microstepping settings.``

What this means is that you're motor dependent - not stepper-setting
dependent. Which makes sense, since *Redeem sets the stepping mode*! So
it only needs to know how much current you need, and what kind of motors
are connected. If you need to figure out how many teeth your pulleys
have, use `this page <http://prusaprinters.org/calculator/>`__ to try
out various settings until you get the same number of steps as your
marlin configuration. Once you have the right number of teeth on the
pulley set, change the step from 1/16th or 1/32nd to be 1/1 (full steps)
for Redeem, and use the value of steps per mm it gives you in your
local.cfg.

If you have a geared motor to run your extruder, I suggest you first
find the step size for your other motors (assuming they're all the same
type!) and just multiply by the ratio between your normal and geared
motor in Marlin to set the redeem value. With the example here, Marlin's
200 microsteps per mm with 18 teeth pulleys and 1/32nd stepping gives
you 5.56 (full)steps per mm for Redeem. Marlin's example here shows 900
microsteps per mm, so, 900/200 = 4.5. So Redeem's configuration for the
extruder is 5.56 \* 4.5 = 25.02 (full)steps per mm.

Bed leveling probe
~~~~~~~~~~~~~~~~~~

Whether you have a delta or cartesian, you may want to be able to use
your Z-probe. In Marlin, a z-probe is defined with a few entries in the
config file, the rest is done for you:

| ``#define AUTOLEVEL_GRID 24  // Distance between autolevel Z probing points, should be less than print surface radius/3.``
| ``#define Z_PROBE_OFFSET {5, 15, -1.17, 0}  // X, Y, Z, E distance between hotend nozzle and deployed bed leveling probe.``

Some newer versions may have a few additional parameters about where to
go to deploy/retract the probe, but that's basically it.

To add those mechanical values in your local.cfg, add the following
section:

| ``[Probe]``
| ``offset_x = 0.005``
| ``offset_y = 0.015``
| ``offset_z = -0.0017``

**TODO (discussion with sniffle on Slack:)** **so jon\_c if you want to
add this to that todo document basically for now,
home\_backoff\_offset\_z = xxx is roughly the same as making adjustments
to z-probe offset or using M851 in marlin**

To define the probing, it's a bit more complex. For one thing, the
endstop to which your Z-probe is connected to isn't actively listened to
by Redeem during normal operation. You need to enable it. And, if you
have an inductive probe, you also need to power it up. And you need to
redefine what the G29 code does. See
`Redeem#Implemented\_Gcodes <Redeem#Implemented_Gcodes>`__ for some
useful information.

You're basically going to redefine G29 using Macros. You can also
simplify your life by defining a probe deployment macro (G32) and probe
retraction macro (G31). This is my current macro section, for a Kossel
Mini with a mechanical endstop switch being flipped into place before,
and flipped back out of the way after the probing is complete.

| ``[Macros]``
| ``g32 =``
| ``        M574 Z2 x_ccw,y_ccw,z_ccw ; configure the Z2 endstop to be active, including which way the motors should spin upon endstop hit.``
| ``        G1 Z5 F4000``
| ``        G1 X50 Y-25``
| ``        G1 Z28``
| ``        G1 X0 Y0``
| ``g31 =``
| ``        M574 Z2 ; deactivate any endstop input from the probe after probing is competed.``
| ``        G1 X0 Y0``
| ``        G1 Z50``
| ``        G1 X50 Y-25``
| ``        G1 Z30``
| ``        G1 X0 Y0 Z35``
| ``        G1 Z250``
| ``g29 =``
| ``        G28 ; home the printer head``
| ``        M561``
| ``        M558 P3``
| ``        M557 P0 X0   Y0   Z5``
| ``        M557 P1 X50  Y0   Z5  ; Set probe point``
| ``        M557 P2 X0   Y50  Z5  ; Set probe point``
| ``        M557 P3 X-50 Y0   Z5  ; Set probe point``
| ``        M557 P4 X0   Y-40 Z5  ; Set probe point``
| ``        M557 P5 X25  Y0   Z5``
| ``        M557 P6 X0   Y25  Z5``
| ``        M557 P7 X-25 Y0   Z5``
| ``        M557 P8 X0   Y-25 Z5``
| ``        M500``
| ``        G32 ; deploy the Z-probe``
| ``        G30 P0 S``
| ``        G30 P1 S              ; Probe point 1``
| ``        G30 P2 S              ; Probe point 2``
| ``        G30 P3 S              ; Probe point 3``
| ``        G30 P4 S              ; Probe point 4``
| ``        G30 P5 S``
| ``        G30 P6 S``
| ``        G30 P7 S``
| ``        G30 P8 S``
| ``        G31                   ; retract the probe``

Delta printers
~~~~~~~~~~~~~~

Assuming your mechanics for your arduino mega-like board were soundly
calibrated and nothing changed when you plugged it into the replicape
instead, you should be able to look at the configuration file you had
for Marlin and extract some of the useful values and put them in your
Redeem's local.cfg file to help you get started faster.

the delta values
^^^^^^^^^^^^^^^^

Your delta values in Marlin should look something like this:

| ``#define DELTA``
| ``// Make delta curves from many straight lines (linear interpolation).``
| ``// This is a trade-off between visible corners (not enough segments)``
| ``// and processor overload (too many expensive sqrt calls).``
| ``#define DELTA_SEGMENTS_PER_SECOND 90``
| ``// Center-to-center distance of the holes in the diagonal push rods.``
| ``#define DELTA_DIAGONAL_ROD 214.0 // mm``
| ``// Horizontal offset from middle of printer to smooth rod center.``
| ``#define DELTA_SMOOTH_ROD_OFFSET 145.0 // mm``
| ``// Horizontal offset of the universal joints on the end effector.``
| ``#define DELTA_EFFECTOR_OFFSET 19.9 // mm``
| ``// Horizontal offset of the universal joints on the carriages.``
| ``#define DELTA_CARRIAGE_OFFSET 19.5 // mm``
| ``// Effective horizontal distance bridged by diagonal push rods.``
| ``#define DELTA_RADIUS (DELTA_SMOOTH_ROD_OFFSET-DELTA_EFFECTOR_OFFSET-DELTA_CARRIAGE_OFFSET)``
| ``// Effective X/Y positions of the three vertical towers.``
| ``#define SIN_60 0.8660254037844386``
| ``#define COS_60 0.5``
| ``#define DELTA_TOWER1_X -SIN_60*DELTA_RADIUS // front left tower``
| ``#define DELTA_TOWER1_Y -COS_60*DELTA_RADIUS``
| ``#define DELTA_TOWER2_X SIN_60*DELTA_RADIUS // front right tower``
| ``#define DELTA_TOWER2_Y -COS_60*DELTA_RADIUS``
| ``#define DELTA_TOWER3_X 0.0 // back middle tower``
| ``#define DELTA_TOWER3_Y DELTA_RADIUS``
| ``// Diagonal rod squared``
| ``#define DELTA_DIAGONAL_ROD_2 pow(DELTA_DIAGONAL_ROD,2)``

Now, in redeem, the file you want to be putting those values in is:

``/etc/redeem/local.cfg``

Elias has already normally properly set the values for the Kossel Mini
in the kosselmini.cfg redeem profile. But if you have another delta,
you'll need to overwrite those values with the equivalent from Marlin.

But! Remember, **Redeem uses meters, not millimeters** as the default
unit! So you'll need to divide every value in Marlin by 1000.

Endstops and home position
^^^^^^^^^^^^^^^^^^^^^^^^^^

To define the home position on a Delta, which is typically (x,y,z) =
(0,0,h) where h is the top of the the printer's moving space, you'll
want to set the parameters in your local.cfg (note that all section
headers are case sensitive) like so:

::

    [Homing]
    home_x = 0
    home_y = 0
    home_z = h
    home_speed_x = 0.2
    home_speed_y = 0.2
    home_speed_z = 0.2
    home_speed_e = 0.2
    home_speed_h = 0.2

Remember to set the **h** to the value *converted in meters* you had
stored under the value

``#define MANUAL_Z_HOME_POS 251.20``

in Marlin.

The home\_speed values are given in **meters per second**! Do not
casually change those to the values you had in Marlin or you will have
bits and pieces flying off into orbit.