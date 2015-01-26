"""
GCode M104
Set extruder temperature

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import logging


class M104(GCodeCommand):

    def execute(self, g):
        if g.has_letter("P"):  # Set hotend temp based on the P-param
            if int(g.get_value_by_letter("P")) == 0:
                target = float(g.get_value_by_letter("S"))
                logging.debug("setting ext 0 temp to " + str(target))
                self.printer.heaters['E'].set_target_temperature(target)
            elif int(g.get_value_by_letter("P")) == 1:
                target = float(g.get_value_by_letter("S"))
                logging.debug("setting ext 1 temp to " + str(target))
                self.printer.heaters['H'].set_target_temperature(target)
        elif g.has_letter("T"):  # Set hotend temp based on the T-param
            if int(g.get_value_by_letter("T")) == 0:
                target = float(g.get_value_by_letter("S"))
                logging.debug("setting ext 0 temp to " + str(target))
                self.printer.heaters['E'].set_target_temperature(target)
            elif int(g.get_value_by_letter("T")) == 1:
                target = float(g.get_value_by_letter("S"))
                logging.debug("setting ext 1 temp to " + str(target))
                self.printer.heaters['H'].set_target_temperature(target)
        else:  # Change hotend temperature based on the chosen tool
            if self.printer.current_tool == "E":
                target = float(g.token_value(0))
                logging.debug("setting ext 0 temp to " + str(target))
                self.printer.heaters['E'].set_target_temperature(target)
            elif self.printer.current_tool == "H":
                target = float(g.token_value(0))
                logging.debug("setting ext 1 temp to " + str(target))
                self.printer.heaters['H'].set_target_temperature(target)

    def get_description(self):
        return "Set extruder temperature"

    def is_buffered(self):
        return True
