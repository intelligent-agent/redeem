BLTouch
=======

BLTouch is a simple-to-use bed probe from the folks at ANTCLabs. It's
simple because it senses and moves a probe-pin with an electromagnet,
which gives it a very small footprint and makes it easy to mount onto
different printers. You can find out more on `the IndieGoGo
page <https://www.indiegogo.com/projects/bltouch-auto-bed-leveling-sensor-for-3d-printers#/>`__

BLTouch is a bit harder to set up in software because it pretends to be
both an endstop and a servo. The servo interface is used to deploy and
retract the pin, and the endstop interface conveys when the pin hits the
bed. The endstop interface is also a bit tricky because it isn't
persistent - the pin triggers, the endstop sends a 5ms pulse, then the
device resets.

Use with Redeem
---------------

It is currently recommended to use the BLTouch with the develop branch
of Redeem because the new PRU firmware therein is much more tolerant of
the short pulse-time of the BLTouch. Either way, though, your BLTouch
needs to be connected to an endstop input of your choice and the X2 or
Y2 pins for the servo half. See `Redeem#Servos <Redeem#Servos>`__ to
learn more about that.

On Replicape/Redeem, BLTouch is support for probing but not homing
because it only sends pulses. Homing is theoretically possible but
currently not implemented - feel free to file an issue at `the issue
tracker <https://github.com/intelligent-agent/redeem/issues>`__ if
this is something you could use.

Assuming you plug the servo input into X2 (being careful to match up the
data/ground/5v pins according to
`Replicape\_rev\_B#Fritzing\_example <Replicape_rev_B#Fritzing_example>`__),
your servo config should look like this:

::

    [Servos]
    servo_0_enable = True
    servo_0_channel = P9_14
    servo_0_angle_init = 90
    servo_0_angle_min = 0
    servo_0_angle_max = 180
    servo_0_pulse_min = 0.0006
    servo_0_pulse_max = 0.0024

Make sure to also add an appropriate endstop config. On a delta where
the BLTouch's endstop half is connected to Z2, that would look like
this:

::

    [Endstops]
    end_stop_z2_stops = x_neg, y_neg, z_neg

A cartesian only needs to block the Z axis like this:

::

    [Endstops]
    end_stop_z2_stops = z_neg

Commands for BLTouch:

| ``M280 P0 S10 F5000 R ; Pin Down``
| ``M280 P0 S90 F5000 R ; Pin Up``
| ``M280 P0 S120 F5000 R ; Self Test``
| ``M280 P0 S160 F5000 R ; Reset Error``

-  If your BLTouch is flashing after startup, use the “Reset Error”
   command above to reset to normal... also, by adding this command to
   your <*GCODE Scripts*><*After connection to printer is established*>
   List, the error will automatically be reset at startup.