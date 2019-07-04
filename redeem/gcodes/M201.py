"""
GCode M202 & M201  - set acceleration

Author: Boris Lasic
email: boris(at)max(dot)si
Website: http://www.max.si
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

import logging
from .GCodeCommand import GCodeCommand


class M201(GCodeCommand):
  def execute(self, g):
    for i, axis in enumerate(self.printer.AXES):
      if g.has_letter(axis):
        self.printer.acceleration[i] = round(g.get_distance_by_letter(axis) / 3600.0, 4)

    if self.printer.axis_config == self.printer.AXIS_CONFIG_CORE_XY or self.printer.axis_config == self.printer.AXIS_CONFIG_H_BELT:
      # x and y should have same accelerations for lines to be straight
      self.printer.acceleration[1] = self.printer.acceleration[0]
    elif self.printer.axis_config == self.printer.AXIS_CONFIG_DELTA:
      # Delta should have same accelerations on all main axes
      self.printer.acceleration[1] = self.printer.acceleration[0]
      self.printer.acceleration[2] = self.printer.acceleration[0]

    self.printer.path_planner.native_planner.setAcceleration(tuple(self.printer.acceleration))

  def get_description(self):
    return "Set print acceleration"

  # todo: fix the description of the units.
  def get_long_description(self):
    return ("""
Sets the acceleration that axes can do in units/minute^2 for print moves.
Example: M201 X1000 Y1000 Z100 E2000"

Values get rounded to nearest whole number, in current G20/21 units.
For CoreXY and HJ-belt mechines, Y value is forced to that supplied for X (Y is ignored).
For Delta machines, X and Y values are forced to that supplied for X (Y and Z are ignored).
In all cases, axes H, A, B and C remain independent.
""")

  def is_buffered(self):
    return False
