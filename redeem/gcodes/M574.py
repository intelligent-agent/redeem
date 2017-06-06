"""
M574: set endstop action
Author: Elias Bakken
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
from redeem.Printer import Printer
import logging
import os

class M574(GCodeCommand):

    def execute(self, g):
        tokens = g.get_tokens()
        logging.debug("end stop tokens: "+str(tokens))

        if len(tokens) > 0:
            es = tokens[0]
            
            config = ""
            index = 1
            while index < len(tokens):
                if tokens[index][0] not in Printer.AXES:
                    raise ValueError("Invalid endstop axis: "+tokens[index])
                
                if len(tokens[index]) > 1:
                    # The axis has a number after it - use that
                    value = float(tokens[index][1::])
                    if value < 0:
                        config += tokens[index][0].lower()+"_neg,"
                    elif value > 0:
                        config += tokens[index][0].lower()+"_pos,"
                    else:
                        raise ValueError("Non-directional endstops aren't supported... yet")
                    index += 1
                else:
                    if len(tokens) >= index + 4:
                        if ''.join(tokens[index + 1 : index + 4]).lower() == "neg":
                            config += tokens[index][0].lower()+"_neg,"
                        elif ''.join(tokens[index + 1 : index + 4]).lower() == "pos":
                            config += tokens[index][0].lower()+"_pos,"
                        else:
                            raise ValueError("Can't parse endstop direction suffix: "+tokens[index + 1::])
                        index += 4
                    else:
                        raise ValueError("Endstop direction suffix is too short: "+tokens[index + 1::])
             
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
