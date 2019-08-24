"""
GCode M909
Set microstepping mode

Author: Elias Bakken
email: elias.bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

import logging
from .GCodeCommand import GCodeCommand


class M909(GCodeCommand):
  def execute(self, g):
    self.printer.path_planner.wait_until_done()

    for axis in self.printer.AXES:
      if g.has_letter(axis) and g.has_letter_value(axis):
        val = g.get_int_by_letter(axis, -1)
        if val != -1:
          self.printer.steppers[axis].set_microstepping(val)
    self.printer.path_planner.update_steps_pr_meter()
    logging.debug("Updated steps pr meter to %s", self.printer.get_steps_pr_meter())

  def get_description(self):
    return "Set microstepping value"

  def get_long_description(self):
    return (
        "Example: M909 X3 Y5 Z2 E3\n"
        "Set the microstepping value for each of the steppers. What these values mean depends on your board revision. "
    )

  def is_buffered(self):
    return True
