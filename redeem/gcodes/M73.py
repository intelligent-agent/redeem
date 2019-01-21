"""
GCode M73 - STUB
Set current print progress percentage for LCD.
M73 P<percent>

Author: Nathan Reichenberger
email: zaped212(at)gmail(dot)com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

from .GCodeCommand import GCodeCommand
from redeem.Path import Path


class M73(GCodeCommand):
  def execute(self, g):
    #logging.warning("Currently using a stub implementation for M73")
    return

  def get_description(self):
    return "Set current print progress percentage for LCD."

  def get_long_description(self):
    return ("Set current print progress percentage for LCD. "
            "M73 P<percent> where percent is current print progress percentage")
