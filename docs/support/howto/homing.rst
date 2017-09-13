Homing
======

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
