Nomenclature
============

-  For the purposes of documentation, it is assumed that the origin
   (0,0,0) is at the front left of the print bed for Cartesian and
   CoreXY Printers. Typically, it is either front left, or rear right.
   If it is rear right, you can just picture turning the printer 180
   degrees and that will put it in the proper orientation.

-  On a Delta printer, origin is in the center of the bed. Home position
   is at the top, near the endstops.

-  Location of endstops does not mean that your origin is there. It is
   possible to home to X\_Min and Y\_Max or even X\_Max and Y\_Max. If
   in doubt, assume front left on a non-Delta printer, center on a
   Delta, and then print the `Left/Right Orientation Test
   Part <https://www.thingiverse.com/thing:150740>`__. This part should
   print LEFT RIGHT and show if you have your orientation correct.

-  In OctoPrint, on the Control tab, there are a set of arrows that
   control the print head. These move the print head as if the print bed
   were stationary. On the X/Y section, the Up Arrow will move the print
   head away from the origin, towards the back of the printer. Right
   Arrow will move the print head to the right, away from origin. In the
   Z section, the Up Arrow will move the head up away from the print
   bed.

   -  Remember, all movements are as if the print bed is stationary!!

-  End stops: Minimum is at the 0 of that axis. If you home to an end
   stop at the maximum end of the axis, you need to set an offset in
   your Redeem local.cfg so the system knows how far to back off from
   the end stop to reach 0. This is not needed if you home to the
   Minimum end of the axis

``offset_y = 0.15  #Remember, these measurements are in meters``

-  Configuration file precedence: The system will check for a local.cfg
   file first and check if the value it needs is in that file. If it
   doesn't find it there, it will check for a printer.cfg file. Failing
   that, it will check the default.cfg file. It is strongly recommended
   that you make any needed changes in the appropriate local.cfg file,
   as that file does not get overwritten when the software is upgraded.
   Any changes made to printer.cfg or default.cfg may be lost when the
   software is updated. This applies to both Redeem and Toggle

-  Configuration file format: You do need the appropriate section
   headers (in brackets) when you add config options.

| ``[Geometry]``
| ``axis_config = 2``
| ``travel_x = 0.35``
| ``travel_y = 0.25``
| ``travel_z = 0.4``

-  Recommended order of setup: Make sure your axis movements are in the
   correct direction first. It does no good to set up your endstops and
   homing if your Y axis is moving the wrong way. Remember, all
   movements are in relation to a stationary print bed, so if you have a
   print bed that moves downward (such as a CoreXY design), clicking the
   Z Up arrow will move the bed DOWN.