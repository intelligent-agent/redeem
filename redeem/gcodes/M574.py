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

class M574(GCodeCommand):

    def execute(self, g):
        tokens = g.get_tokens()
        if len(tokens) > 0:
            es = tokens[0]
            config = tokens[1] if len(tokens) > 1 else ""

            if not es in self.printer.end_stops:
                logging.warning("M574: Wrong end stop: "+str(es))
            
            logging.debug("Setting end stop config for "+str(es)+" to "+str(config))
        
            self.printer.path_planner.wait_until_done()

            # Set end stop config
            self.printer.end_stops[es].stops = config

            # Update the config.
            self.printer.config.set('Endstops', 'end_stop_'+es+'_stops', config)

            # Save the config file. 
            self.printer.config.save('/etc/redeem/local.cfg')

            # Recompile the firmware
            self.printer.path_planner.pru_firmware.produce_firmware()

            # Restart the path planner. 
            self.printer.path_planner.restart()
        else:
            g.set_answer("ok "+", ".join([v.name+" stops: "+str(v.stops)+" " for _,v in sorted(self.printer.end_stops.iteritems())]))


    def get_description(self):
        return "Set or get end stop config"

    def get_long_description(self):
        return ("If not tokens are given, return the current end stop config. "
                "To set the end stop config: "
                "This G-code takes one end stop, and one configuration "
                "where the configuration is which stepper motors to stop and "
                "the direction in which to stop it. Example: M574 X1 x_ccw "
                "This will cause the X axis to stop moving in the counter clock wise "
                "direction. Note that this recompiles and restarts the firmware")
