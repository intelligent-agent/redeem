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
