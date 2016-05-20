"""
M574: set endstop action
Author: Elias Bakken
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import logging
import os

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
            self.printer.config.save(os.path.join(self.printer.config_location,'local.cfg'))

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
