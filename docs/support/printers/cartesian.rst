Cartesian Printers
==================

***This is a work in progress, so bare with me... There are tons of
varieties when it comes to Cartesian printers, and this tutorial will be
as complicated to write as it is to set up one of these printers.***

Welcome to the *Setting up Replicape for Cartesian Printers* How-To!!

First off, if this is your first printer, or maybe the first printer
you've built yourself, please just take your time and don't frustrate
yourself. If you thought you were going to be printing on the first day
or even the first week, I hate to break the news, but there is a
learning curve involved. Try to have fun, and don't hesitate to check in
over at:
`Slack <https://www.thing-printer.com/wp-login.php?action=slack-invitation>`__
and
`Google+ <https://plus.google.com/communities/104577360369030938514>`__
if you need some real-time help.

-  I'm hoping you have figured out how to wire your steppers, end stops,
   fans, heaters, etc... I also hope you know your way around Cartesian
   space... from this point on, just remember that on your Cartesian
   printer, the `front left <front_left>`__ corner of your build plate
   is X 'zero', and Y 'zero' (0,0)... and when the tip of your hot end
   is touching your build plate your Z axis is at 'zero'...

-  When you first turn on your printer, the system is going to think
   it's sitting at X 'zero', Y 'zero', Z 'zero' until it homes to it's
   endstops, so until we have the correct configuration, let's only make
   careful moves with the software.

OK! So if your printer is wired up, and you have the software flashed,
let's get started!

Configurations
--------------

Let's open Octoprint and check out the Profile Configurations which are
located in These guys are what tells Redeem (the software) everything it
needs to know about your printer. At the bottom you'll see
*Default.cfg*... Click on the little eyeball and check out all of the
commands in that file. This configuration contains all of the necessary
commands that tells the software the size of the printer, how much power
to send to your steppers, how fast it can move, and how slow, just to
name a few... Ok, close that window... above *Default.cfg*, you'll see
*Printer.cfg*... these particular configurations are tweaked for
specific printers, and whatever is written to this configuration will
override the commands within the *Default.cfg*... if you have a name
brand printer or a similar clone, you can choose the configuration that
matches your printer and use it as your default profile. This could get
you to third base with setting up your printer!

Before we go printing, let's talk a little more about that profile up
top called “Local.cfg”... What? There's nothing in that profile? You're
right! This is where you get to add commands to the configuration... and
this configuration overrides the *Printer.cfg*, and the *Default.cfg*,
so now I hope you're seeing the “hierarchy” of the configurations...
*Local.cfg* > *Printer.cfg* > *Default.cfg*...

Setting up your Local.cfg
-------------------------

Setting up your *Local.cfg* can get pretty complicated, but for now,
we're just going to get your printer moving normally, homing correctly,
and stopping where it's supposed to... once you've got your feet wet,
and maybe waste deep, you'll eventually need to dive into some deeper
water to get your printer tweaked for maximum performance... I'll tell
you where to go at the end of this How-To. \*\*Also\*\* Whenever you add
to or make changes to your *Local.cfg*, you'll need to restart Redeem
for those changes to take effect.

For now, let's get started with the basic entries you'll need to get
started!

[System]
~~~~~~~~

Let's leave the *System* section alone for now, but if you're using
Toggle and a Manga Screen or similar, you'll need to edit this section
later to get those systems working. For now, just add:

| ``[System]``

[Geomtery]
~~~~~~~~~~

The *Geometry* section basically lets the software know what kind of
printer it's dealing with. Having a Cartesian printer, you don't even
need this section in your *Local.cfg*, but I've decided to add it
anyway. You can add this section if you want:

::

    [Geometry]
    # 0 - Cartesian
    # 1 - H-belt
    # 2 - Core XY
    # 3 - Delta
    axis_config = 0

[Steppers]
~~~~~~~~~~

The *Steppers* section is where you'll make changes for your stepper's
steps per mm, direction, supplied amperage, microstepping, and whether
or not they're in use. If you have two stepper motors for one axis this
is where you will add the second stepper as a slave... I'll have a
second section for help with the slave stepper. Here are the following
entries you can add to your *Stepper* section with explanations for
each:

::

    [Steppers]
    # steps per mm:
    #   Defined how many stepper full steps needed to move 1mm.
    #   Do not factor in microstepping settings.
    #   For example: If the axis will travel 10mm in one revolution and
    #                angle per step in 1.8deg (200step/rev), steps_pr_mm is 20.
    steps_pr_mm_x = 4.0
    steps_pr_mm_y = 4.0
    steps_pr_mm_z = 50.0
    steps_pr_mm_e = 6.0
    steps_pr_mm_h = 6.0
    steps_pr_mm_a = 6.0
    steps_pr_mm_b = 6.0
    steps_pr_mm_c = 6.0
    # Which steppers are enabled
    in_use_x = True
    in_use_y = True
    in_use_z = True
    in_use_e = True
    in_use_h = True
    in_use_a = False
    in_use_b = False
    in_use_c = False
    # Set to -1 if axis is inverted
    direction_x =  1
    direction_y =  1
    direction_z =  1
    direction_e =  1
    direction_h =  1
    direction_a =  1
    direction_b =  1
    direction_c =  1
    # A stepper controller can operate in slave mode,
    # meaning that it will mirror the position of the
    # specified stepper. Typically, H will mirror Y or Z,
    # in the case of the former, write this: slave_y = H.
    slave_x =
    slave_y =
    slave_z =
    slave_e =
    slave_h =
    slave_a =
    slave_b =
    slave_c =

[Endstops]
~~~~~~~~~~

The first thing we need to do is make sure your endstops are working
correctly... to do this, all you need to do is go into Octoprint and
open the Terminal. When you press in your endstop switches, you should
see a message in the terminal that displays which end stop was hit. If
you're not seeing this message, then

[Homing]
~~~~~~~~

Updated 09/28/17 by: Dancook