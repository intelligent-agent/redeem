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
    from Path import Path
except ImportError:
    from redeem.Stepper import Stepper
    from redeem.Path import Path
import logging

class M909(GCodeCommand):

    def execute(self, g):
        for i in range(g.num_tokens()):
            self.printer.steppers[g.token_letter(i)].set_microstepping(int(g.token_value(i)))
        # Update the steps pr m in the native planner. 
        self.printer.path_planner.native_planner.setAxisStepsPerMeter(tuple([long(Path.steps_pr_meter[i]) for i in range(3)]))
        logging.debug("Updated steps pr meter to "+str(Path.steps_pr_meter))
        # Update the extruders
        for i in range(Path.NUM_AXES - 3):
            e = self.printer.path_planner.native_planner.getExtruder(i)
            e.setAxisStepsPerMeter(long(Path.steps_pr_meter[i + 3]))

    def get_description(self):
        return "Set stepper microstepping settings"

    def get_long_description(self):
        return ("Example: M909 X3 Y5 Z2 E3"
                "Set the microstepping value for"
                "each of the steppers. In Redeem this is implemented"
                "as 2^value, so M909 X2 sets microstepping "
                "to 2^2 = 4, M909 Y3 sets microstepping to 2^3 = 8 etc. ")

 
