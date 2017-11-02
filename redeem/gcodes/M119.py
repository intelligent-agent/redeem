"""
GCode M119
Get current endstops state

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import logging
import os
from six import iteritems


class M119(GCodeCommand):
    def execute(self, g):
        tokens = g.get_tokens()
        if len(tokens) > 1:
            es = tokens[0]
            val = tokens[1]
            if not es in self.printer.end_stops:
                logging.warning("M119: Wrong end stop: "+str(es))
                return
            if val not in ["S0", "S1"]: 
                logging.warning("M119: Invalid invert value for " \
                    "end stop {}: {}. Use S0, to univert or S1, to invert".format(es, val))
                return
            val = bool(int(val[1]))
            logging.info("Setting end stop inversion for "+str(es)+" to "+str(val))
            self.printer.end_stops[es].invert = val
            
            self.printer.path_planner.wait_until_done()
            # Update the config.
            self.printer.config.set('Endstops', 'invert_'+es, str(val))

            # Save the config file. 
            self.printer.config.save(os.path.join(self.printer.config_location,'local.cfg'))

            # Recompile the firmware
            self.printer.path_planner.pru_firmware.produce_firmware()

            # Restart the path planner. 
            self.printer.path_planner.restart()

            # Read the value again to update current state
            self.printer.end_stops[es].read_value()
            endstop = self.printer.end_stops[es]
            logging.info("Is {} hit? {}, inverted? {}".format(es, endstop.hit, endstop.invert))
        else:
            g.set_answer("ok "+", ".join([v.name+": "+str(v.hit) for _,v in sorted(iteritems(self.printer.end_stops))]))

    def get_description(self):
        return "Get current endstops state or set invert setting"    

    def get_long_description(self):
        return "Get endstops state or set invert state of an endstop. "\
                "If two tokens are supplied, the first must be a single end stop and "\
                "the second either S1 or S0, to invert or un-invert that endstop, respectively."\
                "Ex: 'M119 X1 S1', to invert end stop X1"
