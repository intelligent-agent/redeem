Delta Printers
==============

..  role:: todo

Before I start this tutorial, one very important detail to know before
you start stripping wires and cranking on your Delta is:

- X-axis in the back
- Y-axis to the left
- Z-axis to the right

My goal here is to give a quick rundown of how to get your Delta moving
correctly, homing, and then autocalibrated... If you need help with
wiring, WiFi, SSH'ing into your BBB, or generally linking your printer
with Octoprint there is plenty of documentation within the Wiki, and we
also have plenty of skilled guys over at:
`Slack <https://www.thing-printer.com/wp-login.php?action=slack-invitation>`__
and
`Google+ <https://plus.google.com/communities/104577360369030938514>`__
to offer help. I also suggest you take some time to look over all of the
G/MCodes and Redeem in general over at
http://wiki.thing-printer.com/index.php?title=Redeem

OK, so you have your towers figured out? **Good..** and you've wired
everything up to the best of your knowledge? **Great!** Your printer is
connected to Octoprint? **Fantastic!**

Profile Configurations
----------------------

Ok, let's wrap our brains around the Profile Configurations which are
located in These guys are what tells Redeem (the software) everything it
needs to know about your printer. At the bottom you'll see
*Default.cfg*... Click on the little eyeball and check out all of the
commands in that file. This configuration contains all of the necessary
commands that tells the software the size of the printer, how much power
to send to your steppers, how fast it can move, and how slow, just to
name a few... Ok, close that window... above *Default.cfg*, you'll see
*Printer.cfg*... these particular configurations are tweaked for
specific printers, and whatever is written to this configuration will
override the commands within the *Default.cfg*... you with me so far?
Excellent! Beers for everyone! Wait, we're not finished yet! You may
have noticed that you can't make any changes to those two
configurations, and that's a good thing, let me tell you! “Default.cfg”
lives up to it's name and has a full list of the available commands for
your printer... when the time comes, you can copy/paste those commands
to your “Local.cfg” and tweak those commands to suit your printer.

OK... if you have a typical off the shelf delta printer like a Kossel
Mini, you're in luck! Look for *Kossel Mini* in the list of
configurations under *Printer.cfg* and make it your default
configuration by clicking the star symbol... things should be very close
up to this point... but before we go printing, let's talk a little more
about that profile up top called “local.cfg”... What? There's nothing in
that file? You're right! Something must be wrong... Let me find that
toll free hot-line... Just kidding... this is where you, yes, you get to
make changes to the configuration... and this configuration overrides
the *Printer.cfg*, and the *Default.cfg*, so make sure you're not too
pickled while you're dealing with this config! So does all of that make
sense? The “hierarchy” *Local.cfg* > *Printer.cfg* > *Default.cfg*...

**OK... let's get to the fun stuff!**

Editing Local.cfg
-----------------

So let's say you're the adventurous type, and you've built yourself an
oversized custom delta... 300mm bed, 1M tall...

Before we open up the local.cfg, lets go to “Terminal” tab in Octoprint
and make sure your XYZ endstops are wired correctly... Remembering the
tower positions of XYZ up above, you should see a notification pop up in
the terminal when you manually push the endstops... “X1 Endstop hit” “Y1
Endstop hit” “Z1 Endstop Hit”... if you see this notification for each
endstop, then great! We're on the right track. If not, we're going to
fix them in the [Endstop] section of your local.cfg... if they don't
work after that, then you may have wired them incorrectly!

Let's open up our local.cfg file in Octoprint and start from the top
with what you will need to enter initially... **Do not copy/paste
anything within parentheses... these are only explanations...**

::

    [Geometry]

    axis_config = 3 (The 3 here means that we are using a Delta printer... 0 would be used for normal Cartesian)


:ref:`ConfigStepperMicrostepping`

::

    [Steppers]

    microstepping_x = 3 (The 3 here means we are microstepping at 1/4 steps for each stepper...)
    microstepping_y = 3
    microstepping_z = 3
    microstepping_e = 3


    current_x = 0.5 (This setting is 0.5 amps... anything above this will require cooling and the addition of heat sinks...)
    current_y = 0.5 (I would highly recommend adding heatsinks to the stepper drivers and a fan for cooling the board...)
    current_z = 0.5 (There will probably come a time when you need more current, which requires mandatory cooling...)
    current_e = 0.5

`Calibrating your extruder`__

__  https://toms3d.org/2014/04/06/3d-printing-guides-calibrating-your-extruder

::

    steps_pr_mm_x = 5.0 (This should get you in the ballpark with 1.8 degree steppers...)
    steps_pr_mm_y = 5.0 (When the time comes, you will need to calibrate your X, Y, and Z for accurate prints)
    steps_pr_mm_z = 5.0
    steps_pr_mm_e = 6.0 (You will need to calibrate your steps here... see: 
    in_use_x = True (By adding ``\ “``True``”\ `` here, it means that you do have a stepper in use for this axis...)
    in_use_y = True
    in_use_z = True
    in_use_e = True
    direction_x = 1 (You can change direction of your steppers by entering -1 but I suggest when you)
    direction_y = 1 (wire your steppers, have them all connected to the Replicape so that they are all)
    direction_z = 1 (wired and connected identically


    ``[Endstops]``
    has_x = True (Chances are, you have an endstop for each of these axes... therefore ``\ “``True``”\ ``!)
    has_y = True
    has_z = True

    end_stop_x1_stops = x_cw (Most deltas will have the endstop stopping the cw rotation of your stepper...
    end_stop_y1_stops = y_cw (but if yours is different, change it to ``\ “``ccw``”\ ``... I also suggest having all of your steppers)
    end_stop_z1_stops = z_cw (rotating in the same direction... things get confusing otherwise)
    soft_end_stop_min_x = -0.150 (Since X0 and Y0 are in the center, you'll use a negative radius for minimum X and Y,)
    soft_end_stop_min_y = -0.150
    soft_end_stop_max_x = 0.150 (And a positive radius for your maximum X and Y...)
    soft_end_stop_max_y = 0.150
    invert_x1 = False (Remembering your X,Y,Z tower positions mentioned above... if everything was working, then we can leave)
    invert_y1 = False (these as "False... If you weren't receiving the ``\ “``Endstop``\ `` ``\ ``hit``”\ `` notifications, then change this to ``\ “``True``”\ ``... save your)
    invert_z1 = False (local.cfg, restart Redeem, and check them again manually...)

Ok... back to Endstops... if you had the “Endstop hit” notifications in
your *Terminal* then you can move on to the next step... however, if you
didn't get the notifications, change the “invert\_x1/y1/z1 =” from
“False” to “True” and check the *Terminal* again for the notifications
after restarting Redeem.

At this point, you should be able to save your changes in the local.cfg,
restart Redeem, and at least get movement from your machine... once
you're reconnected to Octoprint, go to your *Terminal* tab and enter M18
(to disengage your steppers). Physically move your printhead so that
your carriages are at about half the distance to your endstops. The
software is going to think you're Z axis is at “0”, so enter G1 Z20 and
see if all three motors are raising the carriages. If any of your
carriages are moving down, then I suggest physically flipping the plug
connecting that stepper to the Replicape. To be safe, power down the
machine beforehand... remove the plug, flip it 180°, and plug it back
in. Do this for any steppers that were not moving upwards. Once
finished, power up your machine and check the movement again just like
before.

If your machine was working correctly, then you're ready to move on to
the next step!!

Checking Your Endstops
----------------------

OK... if your machine is moving as it should, let's open up the
*Terminal* once more and enter M18 again to disengage the steppers.
Physically move the printhead near bottom center and then enter “G92
Z0”... this will zero your Z axis so we can use the next command... now
enter “G1 Z75 F1000”... this should be enough movement at a slow enough
speed for you to physically press the endstop switches before it stops.
Theoretically with our current local.cfg, there shouldn't be a problem,
and I need to investigate further before going much further with
suggestions if they aren't... I'd say refer to this section of the
original wiki:
http://wiki.thing-printer.com/index.php?title=Redeem#Steppers ... if
your endstops are working correctly, then let's move on!

If you've made it this far, then congratulations! The easy stuff is
basically finished... Now we need to get your delta to home properly.
Let's start by adding a [Homing] section to your local.cfg

Homing Properly
---------------

::

    [Homing]
    home_x = 0.0 (Home is at center X)
    home_y = 0.0 (Home is at center Y)
    home_z = 0.200 (This homes Z towards the top... once you have your endstop offsets, we'll change this number to pull off of the endstops)
    home_e = 0.0 (Homes extruder to 0)
    home_speed_x = 0.08 (This moves your stepper at 80mm/s during the homing routine)
    home_speed_y = 0.08 (I suggest homing XYZ at the same speed)
    home_speed_z = 0.08 
    home_speed_e = 0.01

With this particular [Homing] set up, if you enter “G28” at the
*Terminal*, your carriages should move up until they hit the endstops.
It will think your endstops are at 200mm from the bed until you have
your “endstop offsets” set up... we'll get into that later. I've set
this number to 0.200 in hopes to keep you from accidentally smashing
your hotend into your bed. If you want, try entering “G1 Z100” then “G1
Z50”... Your tip should be a safe distance from the bed, so I suggest
continuing by using the Octoprint *Control Panel* to move the tip down
by 10mm and on to 1mm and 0.1mm until it's just above the bed by 1mm or
so. Once it's there, you can go to the *Terminal* in Octoprint and enter
“M114” to get the position of your Z axis... change the negative to
positive and add that number to 0.200... you now know approximately what
your total height between your bed and endstops is. You can enter this
new number as your “home\_z” in the [Homing] section of your local.cfg
for now. Don't forget to restart Redeem after making any changes to the
local.cfg. If you'd like to check your new “home\_z” entry, you can home
(G28) your printer and try moving the print head again in small moves
towards the bed until you get to “G1 Z0”... if we did it correctly, you
should be right above the bed by 1mm or so. Good job!

Using Autocalibration “G33”
---------------------------

OK, we're doing great, but we're still not ready to print. There are a
few more very important steps to take before your delta will be anywhere
close to being able to print successfully. At this point we need to get
into calibrating your delta. I suggest getting yourself a probing system
of some kind if you haven't already... BLTouch, FSR system, a servo with
a switch, etc... I won't go into detail with “how-to's” on installing
these systems... if you already have a probing system, then great! We
can continue! If not, then do some research and come back ;-) I'm using
FSR's currently, and have a BLTouch that I plan to start using. I'll add
info here in the future about the BLTouch. These systems are super
cheap, and if you're new to all of this, your chances of successfully
printing without one is pretty slim.

FSR's... super easy to use... if you've found a way to mount them below
your bed, they work great. Another option is physically holding the FSR
and allowing it to get squeezed between your hotend and bed... whatever
the case, use caution not to drive your hotend through your bed! We take
no responsibilty! **One quick note...** If you're using a JohnSL FSR
system, I'm pretty sure you'll need to use a jumper on the NO pins for
it to work properly with the Replicape. Make sure to connect your FSR to
the Z2 Endstop connection of your Replicape... Let's open our local.cfg
once again and go down to the [Endstop] section. Let's add the following
command there:

``end_stop_z2_stops = x_ccw,y_ccw,z_ccw``

Just like the other endstops, once you've restarted Redeem, let's go to
the *Terminal* within Octoprint and make sure we see the notification
“Z2 Endstop Hit” while pressing the FSR... if you see the notification,
then hopefully we have everything connected properly. Home your Z-axis
to the top, and enter “G1 Z50”... while it's heading down, press on the
FSR and see if the printhead stops moving. If it does, then we're in
good shape! Theoretically with our configuration so far, it should work.
If it's not working, check your wiring, and you can enter “M574” in the *Terminal*
to make sure your endstops are activated.

If your probing system is working properly, then we're ready to
Autocalibrate your machine! The first thing we need to do is go into the
*Terminal* and use the G29C command to generate a circular probing
pattern. We also need to give the machine some information so it can
properly set this pattern for us. Here's a breakdown of how to use G29C
from :ref:`G29`:

::

    Generate a circular G29 Probing pattern
    D = bed_diameter_mm, default: 140
    C = Circles, default = 2
    P = points_pr_circle, default: 8
    S = probe_start_height, default: 6.0
    Z = add_zero, default = 1
    K = probe_speed, default: 3000.0

Here's what I suggest for a 300mm bed:

::

    G29C D250 C2 P8 S15 Z1 K1500

This will give you slightly longer and slower moves, and it keeps the
probe from getting to far to the edges. Once you've run this routine,
you're going to see a new section added to your local.cfg called
[Macros] and your new G29 routine will be in this section.

G31/32 Macros
-------------

Now that you have the routine in place, we need to add two more small
macros to your [Macros] section in order for the autocalibration routine
to work properly... what I'm offering here is specific to the JohnSL FSR
system, so you may need to figure this out for your system.

Add the following to your [Macros]:

::

    G32 = 
       M574 Z2 x_ccw,y_ccw,z_ccw        ; Enable FSR System.
    G31 = 
       M574 Z2        ; Disable FSR System.

This can go above or below the G29 routine. These two macros are used
within the G29 routine to enable and disable your FSR system.

Once all of this information is entered in the local.cfg, you're ready
to run your autocalibration command! Of course you'll need to restart
Redeem, and once everything is ready, just go to the *Terminal* and
enter “G33”... **Caution!** If you're manually using your FSR pad, get
ready to place it in the path of the tip! You don't want your nice new
bed or hotend to be damaged! Once autocalibration is finished, you can
enter “M500” into your *Terminal* and your printer will be 99% ready to
print! You're going to see a few things automatically added to your
local.cfg... You'll see a new [Delta] section that looks similar to
this:

:todo:`update based on 2.1.1 configuration`

| **``[Delta]``**
| ``hez = 0.0``
| ``l = 0.288``
| ``r = 0.145606041232``
| ``ae = 0.0``
| ``be = 0.0``
| ``ce = 0.0``
| ``a_tangential = 0``
| ``a_radial = 0.0``
| ``b_radial = 0.0``
| ``c_radial = 0.0``

And you'll also see offsets similar to these added to your [Geometry]
section:

| ``offset_x = -0.316440484471``
| ``offset_y = -0.31603573114``
| ``offset_z = -0.316766815853``

You may also notice that your Z2 endstop just says “end\_stop\_z2\_stops
=” with no entry... that's because your macro has cleared it out, and
that is normal. Otherwise, this endstop would be engaged while you are
printing and causing all kinds of trouble!

You also need to change your “home\_z = 0.xxx” to about 10 or 15 mm
lower than your XYZ offsets. This will pull your carriages off of the
endstops which I've been told can create issues. It doesn't hurt to
rerun G33 once you've made this change.

Well, I'm sure I'm forgetting something, or something seems crazy, or
heck, maybe I'm even wrong somewhere! My suggestion is shoot me an email
at 95roverd90@gmail.com, or hitting any of us up on Slack or G+! Don't
hesitate to ask questions!

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
