"""
GCode M909
Set stepper microstepping settings

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
try:
    from Stepper import Stepper
except ImportError:
    from redeem.Stepper import Stepper


class M909(GCodeCommand):

    def execute(self, g):
        for i in range(g.num_tokens()):
            self.printer.steppers[g.token_letter(i)].set_microstepping(int(g.token_value(i)))
        Stepper.commit()

    def get_description(self):
        return "Set stepper microstepping settings"

    def get_long_description(self):
        return ("Example: M909 X3 Y5 Z2 E3"
                "Set the microstepping value for"
                "each of the steppers. In Redeem this is implemented"
                "as 2^value, so M909 X2 sets microstepping "
                "to 2^2 = 4, M909 Y3 sets microstepping to 2^3 = 8 etc. ")

 
