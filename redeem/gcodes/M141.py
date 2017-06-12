"""
GCode M141
Set fan power and PWM frequency

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand


class M141(GCodeCommand):

    def execute(self, g):
        fan = self.printer.fans[g.get_int_by_letter("P")]
        fan.set_PWM_frequency(g.get_int_by_letter("F"))
        fan.set_value(g.get_float_by_letter("S"))

    def get_description(self):
        return "Set fan power and PWM frequency"

    def is_buffered(self):
        return True
