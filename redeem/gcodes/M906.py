"""
GCode M906
Set stepper current in mA

Author: Elias Bakken
email: elias.bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

from .GCodeCommand import GCodeCommand


class M906(GCodeCommand):

    def execute(self, g):
        self.printer.path_planner.wait_until_done()
        
        for i in range(g.num_tokens()):
            axis = g.token_letter(i)
            stepper = self.printer.steppers[axis]

            # Cap at 2.5A and convert to A.
            stepper.set_current_value(min(int(g.token_value(i)), 2500)/1000.0)

    def get_description(self):
        return "Set stepper current in mA"

    def get_long_description(self):
        return ("Set the stepper current. Unit is mA. Typical use is 'M906 X400'."
                "This sets the current to 0.4A on the X stepper motor driver."
                "Can be set for multiple stepper motor drivers at once. ")
