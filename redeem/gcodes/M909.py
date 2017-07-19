"""
GCode M909
Set microstepping mode

Author: Elias Bakken
email: elias.bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
try:
    from Stepper import Stepper
except ImportError:
    from redeem.Stepper import Stepper
import logging


class M909(GCodeCommand):

    def execute(self, g):
        self.printer.path_planner.wait_until_done()
        
        for axis in self.printer.AXES:
            if g.has_letter(axis) and g.has_letter_value(axis):
                val = g.get_int_by_letter(axis, factored=False)
                if val >= 0 and val <= 7:
                    self.printer.steppers[axis].set_microstepping(val)
        self.printer.path_planner.update_steps_pr_meter()
        logging.debug("Updated steps pr meter to %s", self.printer.steps_pr_meter)

    def get_description(self):
        return "Set microstepping value"

    def get_long_description(self):
        return ("Example: M909 X3 Y5 Z2 E3\n"
                "Set the microstepping value for each of the steppers. In "
                "Redeem this is implemented as 2^value, so M909 X2 sets "
                " microstepping to 2^2 = 4, M909 Y3 sets microstepping to "
                "2^3 = 8 etc. ")

    def is_buffered(self):
        return True

