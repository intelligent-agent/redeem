"""
GCode M92
Set number of steps per millimeters for each steppers

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
try:
    from Stepper import Stepper
    from Printer import Printer
except ImportError:
    from redeem.Stepper import Stepper
    from redeem.Printer import Printer
import logging

class M92(GCodeCommand):

    def execute(self, g):
        for i in range(g.num_tokens()):    # Run through all tokens
            axis = g.token_letter(i)        # Get the axis, X, Y, Z or E
            value = float(g.token_value(i))
            if value > 0:
                logging.info("Updating steps pr mm on {} to {}".format(axis, value))
                self.printer.steppers[axis].set_steps_pr_mm(value)
                i = Printer.axis_to_index(axis)
                self.printer.steps_pr_meter[i] = self.printer.steppers[axis].get_steps_pr_meter()
            else: 
                logging.error('Steps per milimeter must be grater than zero.')
        self.printer.path_planner.restart()

    def get_description(self):
        return "Set number of steps per millimeters for each steppers"
