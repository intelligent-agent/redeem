"""
GCode G21
Setting units

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

from .GCodeCommand import GCodeCommand
import logging


class G20(GCodeCommand):
  def execute(self, g):
    self.printer.unit_factor = 25.4
    logging.debug("Set unit_factor to 25.4 (inches)")

  def get_description(self):
    return "Set units to inches"


class G21(GCodeCommand):
  def execute(self, g):
    self.printer.unit_factor = 1.0
    logging.debug("Set unit_factor to 1.0 (millimeters)")

  def get_description(self):
    return "Set units to millimeters"
