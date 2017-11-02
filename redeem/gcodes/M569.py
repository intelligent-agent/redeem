"""
M569: Set or get axis direction values

Example: M569 X1 Y-1

Set the control value for the drive specified by P that sends it forwards 
to the given value in the S field. After sending the example, sending a 1 to X 
(drive 0) will make it go forwards, sending a 0 will make it go backwards. 
Obviously to be used with extreme caution... 

Author: Elias Bakken
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import logging
import os
from six import iteritems


class M569(GCodeCommand):

    def execute(self, g):
        if g.num_tokens() == 0:
            g.set_answer("ok "+", ".join([name+": "+str(stepper.direction)+" "
                for name,stepper in sorted(iteritems(self.printer.steppers))]))
        else:
            for i in range(g.num_tokens()):  # Run through all tokens
                axis = g.token_letter(i)
                value = int(g.token_value(i))
                if not axis in self.printer.steppers:
                    logging.warning("M569: Invalid axis key: %s", axis)
                    return
                if not value in [1, -1]:
                    logging.warning("M569: Invalid direction value. Use either 1 or -1: %d", value)
                    return

                # Update the config.
                self.printer.config.set('Steppers', 'direction_'+axis, str(value))
                self.printer.steppers[axis].direction = int(value)


            # Save the config file. 
            self.printer.config.save(os.path.join(self.printer.config_location,'local.cfg'))

            self.printer.path_planner.wait_until_done()

            # Recompile the firmware
            self.printer.path_planner.pru_firmware.produce_firmware()

            # Restart the path planner. 
            self.printer.path_planner.restart()


    def get_description(self):
        return "Set or get stepper direction"

    def get_long_description(self):
        return ("Set the direction for each axis. "
                "Use <axis><direction> for each of the axes you want."
                "Axis is one of X, Y, Z, E, H, A, B, C and direction is 1 or -1"
                "Note: This will store the result in the local config and restart "
                "the path planner. If no tokens are given, return the current config.")

