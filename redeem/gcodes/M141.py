"""
GCode M141
Set fan power and PWM frequency

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

import logging
from .GCodeCommand import GCodeCommand


class M141(GCodeCommand):
  def execute(self, g):
    if not (g.has_letter("P") and g.has_letter("I") and g.has_letter("S")):
      logging.warning("M141 supplied invalid arguments. P, I and S are required")
      return
    fan = self.printer.fans[g.get_int_by_letter("P")]
    fan.set_PWM_frequency(g.get_int_by_letter("I"))
    fan.set_value(g.get_float_by_letter("S"))

  def get_description(self):
    return "Set fan P, to power S (1.0 = 100%) and PWM frequency I (in Hz).\nex. M141 P0 I1000 S0.5"

  def is_buffered(self):
    return True
