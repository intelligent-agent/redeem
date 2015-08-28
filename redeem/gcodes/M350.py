"""
GCode M350
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


class M350(GCodeCommand):

    def execute(self, g):
        self.printer.path_planner.wait_until_done()
        
        for i in range(g.num_tokens()):
            axis = g.token_letter(i)
            stepper = self.printer.steppers[axis]
            stepper.set_microstepping(int(g.token_value(i)))
        self.printer.path_planner.update_steps_pr_meter()
        Stepper.commit()

    def get_description(self):
        return "Set microstepping mode for the axes present with a token. " \
               "Microstepping will be 2^val. Steps pr. mm. is changed" \
               " accordingly."
