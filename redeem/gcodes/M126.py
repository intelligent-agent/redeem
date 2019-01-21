"""
GCode M126 - STUB
Open the valve for Baricuda paste extruder 1.
M126 [S<pressure>]

Author: Nathan Reichenberger
email: zaped212(at)gmail(dot)com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

from .GCodeCommand import GCodeCommand
from redeem.Path import Path


class M126(GCodeCommand):
  def execute(self, g):
    #logging.warning("Currently using a stub implementation for M126")
    return

  def get_description(self):
    return "Open the valve for Baricuda paste extruder 1."

  def get_long_description(self):
    return ("Open the valve for Baricuda paste extruder 1. "
            "M126 [S<pressure>] where pressure is the valve pressure.")
