"""
GCode M18
Disable all steppers

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

import logging
from GCodeCommand import GCodeCommand
try:
    from Stepper import Stepper
except ImportError:
    from redeem.Stepper import Stepper

class M18(GCodeCommand):

    def execute(self, g):
        logging.debug("Execute M18")
        self.printer.path_planner.wait_until_done()
        if g.has_letter("D"):
            pd = bool(g.get_int_by_letter("D", 0))
            self.printer.steppers["X"].set_stepper_power_down(pd)
        else:
            # If no token is present, disable all steppers
            if g.num_tokens() == 0:
                g.set_tokens(self.printer.steppers.keys())

            for i in range(g.num_tokens()):  # Run through all tokens
                axis = g.token_letter(i)  # Get the axis, X, Y, Z or E
                self.printer.steppers[axis].set_disabled()

    def get_description(self):
        return "Disable all steppers or set power down"

    def get_long_description(self):
        return "Disable all steppers. No more current is applied to the " \
               "stepper motors after this command. "\
               "If only token D is supplied, set power down mode (0 or 1)"

    def is_buffered(self):
        return True
