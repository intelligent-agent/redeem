Homing
======

travel\_\*, offset\_\*, and home\_\* (not in this section, see the
`#Homing <#Homing>`__ section) all make up how a homing routine works.
They can all be positive or negative. Here is a quick run-down of what
is happening internally:

#. If your machine is a delta, switch to cartesian mode.
#. Travel the distance in the opposite direction set in travel\_\*. If an end stop is found, stop.
#. Move away the distance found in backoff\_distance\_\*, then hit the
   end stop once more, slower.
#. Set position to -1 * offset\_\*.
#. If your machine is a delta, switch back to delta mode.
#. Move to home\_\*.

The subtle point to keep in mind when configuring these is that what matters is where your extruder is relative to your bed, not what's moving to get it there. When the extruder is over the front left corner of the printer, it's at X=0, Y=0. It might get there because the extruder moved left and forward, or your extruder could be fixed and the bed moved right and backward instead. The end result is the same - extruder is over the front left corner.

This means that for a traditional cartesian where the extruder moves in X and Y and the bed moves in Z, your config might look like...
::
    [Geometry]
    offset_x = -0.23 # X endstop triggers when the hotend is to the *right* (X+) of the bed
    offset_y = -0.216 # Y endstop triggers when the hotend is to the *rear* (Y+) of the bed
    offset_z = 0.00278 # Z endstop triggers when the bed is at the top of the printer (in this case, it's so high it would hit the hotend if the hotend were in the way)

    # Travel should be roughly the total distance your axes can travel
    travel_x = -0.26 # hotend needs to move *right* (X+) to find its endstop, so negative
    travel_y = -0.26 # hotend needs to move *back* (Y+) to find its endstop, so negative
    travel_z = 0.21 # bed needs to move up towards the hotend (Z-) to find its endstop, so positive

    [Homing]
    home_x = 0.229 # move a bit in from the X endstop at X=0.230
    home_y = 0.100 # move to the middle of the Y axis (endstop was as Y=0.216)
    home_z = 0.01 # move the bed back down

For a Printrbot-like cartesian where the bed moves in X and the extruder moves in Y and Z, your config might look like...
::
    [Geometry]
    offset_x = 0.0 # X endstop triggers when the hotend is to the *left* (X=0) of the bed
    offset_y = -0.150 # Y endstop triggers when the hotend is to the *rear* (Y+) of the bed
    offset_z = -0.000176 # Z endstop triggers when the hotend is just above (but not touching) the bed

    # Travel should be roughly the total distance your axes can travel
    travel_x = 0.16 # hotend needs to move *left* (which is really bed moving right) (X-) to find its endstop, so positive
    travel_y = -0.16 # hotend needs to move *back* (Y+) to find its endstop, so negative
    travel_z = 0.16 # hotend needs to move *down* towards the bed (Z-) to find its endstop, so positive

    [Homing]
    home_x = 0.075 # move to the middle of the X axis
    home_y = 0.075 # move to the middle of the Y axis
    home_z = 0.01 # move a bit up

For a Delta, you would typically have something like...
::
    [Geometry]
    offset_x = -0.250 # endstops are at the top of the towers, so the offsets are negative
    offset_y = -0.250
    offset_z = -0.250

    # Travel should be roughly the height of your printer
    # Endstops are at the tops of the towers, so these values are negative
    travel_x = -0.5
    travel_y = -0.5
    travel_z = -0.5

    [Homing]
    home_x = 0
    home_y = 0
    home_z = 0.200 # home to the center, but keep the effector near the top of the printer


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
