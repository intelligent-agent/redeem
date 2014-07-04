'''
GCode M104
Set extruder temperature

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

from GCodeCommand import GCodeCommand
import logging


class M104(GCodeCommand):

    def execute(self, g):
        if g.has_letter("P"): # Set hotend temp based on the P-param
            if int(g.get_value_by_letter("P")) == 0:
                logging.debug("setting ext 0 temp to "+str(g.get_value_by_letter("S")))
                self.printer.heaters['E'].set_target_temperature(float(g.get_value_by_letter("S")))
            elif int(g.get_value_by_letter("P")) == 1:
                logging.debug("setting ext 1 temp to "+str(g.get_value_by_letter("S")))
                self.printer.heaters['H'].set_target_temperature(float(g.get_value_by_letter("S")))
        else: # Change hotend temperature based on the chosen tool
            if self.printer.current_tool == "E":
                logging.debug("setting ext 0 temp to "+str(g.token_value(0)))
                self.printer.heaters['E'].set_target_temperature(float(g.token_value(0)))
            elif self.printer.current_tool == "H":
                logging.debug("setting ext 1 temp to "+str(g.token_value(0)))
                self.printer.heaters['H'].set_target_temperature(float(g.token_value(0)))

    def get_description(self):
        return "Set extruder temperature"
