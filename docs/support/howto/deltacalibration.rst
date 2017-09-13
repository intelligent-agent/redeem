Delta Calibration
=================

calibrating convex/concave behaviour
------------------------------------

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
--------------------------------

Redeem supports autoprobing the bed
to generate a bed leveling compensation matrix. However it is no
substitute for a poorly setup machine. Try to get your head as level
as possible without bed leveling first, then use the :ref:`g29`
command to generate the fine-tuning bed compensation matrix.

Using G33 for auto-calibration
------------------------------

When you have a working G29 probing setup in place, you can improve
several parameters of your delta printer with the G33 command. The
parameters to improve is end stop offsets, delta radius, tower angular
position correction and diagonal rod length.

G33 will use the probe offset in the [Probe] section to adjust the end
stops offsets, so be sure to set this to 0 initially to avoid offset
errors.

The G33 in Redeem is an implementation of the calculations found in this
web site: http://escher3d.com/pages/wizards/wizarddelta.php
