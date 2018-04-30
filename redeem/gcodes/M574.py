"""
M574: set endstop action
Author: Elias Bakken
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

import os
import logging
from six import iteritems
from .GCodeCommand import GCodeCommand


class M574(GCodeCommand):

    def execute(self, g):
        tokens = g.get_message()[len("M574"):].strip().split(" ")
        if len(tokens) > 0 and tokens[0] != '': # 1st token could be ''
            es = tokens[0].upper()
            config = ""
            for word in tokens[1:]: config += word.replace(",", ", ").lower()

            if not es in self.printer.end_stops:
                logging.warning("M574: Invalid end stop: '%s'", es)
                logging.debug("M574: tokens = "+str(tokens))
                return
            
            logging.debug("Setting end stop config for %s to '%s'", es, config)
        
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
            g.set_answer("ok "+", ".join([v.name+" stops: "+str(v.stops)+" " for _,v in sorted(iteritems(self.printer.end_stops))]))


    def is_buffered(self):
        return True

    def get_description(self):
        return "Set or get end stop config"

    def get_long_description(self):
        return ("If no tokens are given, return the current end stop config. "
                "To set the end stop config: \n"
                "This G-code takes one end stop, and one configuration "
                "where the configuration is which stepper motors to stop and "
                "the direction in which to stop it.\n \n Example:\n"
                "    M574 X1 x_ccw\n"
                "    (The single space separators are required.)\n \n"
                "This will cause the X axis to stop moving in the counter clock wise "
                "direction.\n \n"
                "Note that this recompiles and restarts the firmware.")
