"""
GCode M141
Set fan power and PWM frequency

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import logging

class M141(GCodeCommand):

    def execute(self, g):
        if not (g.has_letter("P") or g.has_letter("F") or g.has_letter("S")):
            logging.warning("M141 supplied invalid arguments. P, F and S are required")
            return
        fan = self.printer.fans[g.get_int_by_letter("P")]
        fan.set_PWM_frequency(g.get_int_by_letter("F"))
        fan.set_value(g.get_float_by_letter("S"))

    def get_description(self):
        return "Set fan P to power S and PWM frequency F. ex. M141 P0 F1000 S0.5"

    def is_buffered(self):
        return True
