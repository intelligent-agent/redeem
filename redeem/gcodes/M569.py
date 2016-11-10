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
import os


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
        return "Set stepper direction"

    def get_long_description(self):
        return ("Set the direction for each axis. "
                "Use <axis><direction> for each of the axes you want."
                "Axis is one of X, Y, Z, E, H, A, B, C and direction is 1 or -1"
                "Note: This will store the result in the local config and restart "
                "the path planner")

