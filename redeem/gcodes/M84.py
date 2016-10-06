"""
GCode M84
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

class M84(GCodeCommand):

    def execute(self, g):
        logging.debug("Execute M84")
        self.printer.path_planner.wait_until_done()
        # If no token is present, disable all steppers
        if g.num_tokens() == 0:
            g.set_tokens(self.printer.steppers.keys())

        for i in range(g.num_tokens()):  # Run through all tokens
            axis = g.token_letter(i)  # Get the axis, X, Y, Z or E
            self.printer.steppers[axis].set_current_disabled()

    def get_description(self):
        return "Set stepper in lowest current mode"

    def get_long_description(self):
        return ("Set each of the steppers with a token to the"
                " lowest possible current mode. This is similar to disable,"
                " but does not actually disable the stepper.")

    def is_buffered(self):
        return True

