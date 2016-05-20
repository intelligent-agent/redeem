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

class M119(GCodeCommand):
    def execute(self, g):
        tokens = g.get_tokens()
        if len(tokens) > 1:
            es = tokens[0]
            val = tokens[1]
            if not es in self.printer.end_stops:
                logging.warning("M119: Wrong end stop: "+str(es))
                return
            if val not in ["0", "1"]: 
                logging.warning("M119: Wrong invert value for " \
                    "end stop {}: {}. Use 0 or 1".format(es, val))
                return
            val = bool(int(val))
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
            g.set_answer("ok "+", ".join([v.name+": "+str(v.hit) for _,v in sorted(self.printer.end_stops.iteritems())]))

    def get_description(self):
        return "Get current endstops state or set invert setting"    

    def get_long_description(self):
        return "Get current endstops state. "\
                "If two tokens are supplied, the first is end stop, "\
                "the second is invert state. "\
                "Ex: M119 X1 1 to invert ends stop X1"
