"""
GCode M907
Set stepper current in A

Author: quillford
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

from .GCodeCommand import GCodeCommand


class M907(GCodeCommand):

    def execute(self, g):
        self.printer.path_planner.wait_until_done()
        
        for i in range(g.num_tokens()):
            axis = g.token_letter(i)
            stepper = self.printer.steppers[axis]

            # Cap at 2.5A and set the current
            stepper.set_current_value(float(min(g.token_value(i), 2.5)))

    def get_description(self):
        return "Set stepper current in A"
