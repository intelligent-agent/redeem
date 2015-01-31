"""
M569: Set axis direction values

Example: M569 X1 Y-1

Set the control value for the drive specified by P that sends it forwards to the given value in the S field. After sending the example, sending a 1 to X (drive 0) will make it go forwards, sending a 0 will make it go backwards. Obviously to be used with extreme caution... 


Set the points at which the bed will be probed to compensate for its plane being slightly out of horizontal. The P value is the index of the point (indices start at 0) and the X and Y values are the position to move extruder 0 to to probe the bed. An implementation should allow a minimum of three points (P0, P1 and P2). This just records the point coordinates; it does not actually do the probing. See G32. 

Author: Elias Bakken
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import logging


class M569(GCodeCommand):

    def execute(self, g):
        for i in range(g.num_tokens()):  # Run through all tokens
            axis = g.token_letter(i)
            value = int(g.token_value(i))
            if not axis in self.printer.steppers:
                logging.warning("M569: Wrong axis key: "+str(axis))
                return
            if not value in [1, -1]:
                logging.warning("M569: Wrong axis value. Use either 1 or -1: "+str(value))
                return

            self.printer.steppers[axis].direction = value

    def get_description(self):
        return "Set stepper direction"

