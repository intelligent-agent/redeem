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
        if not g.has_letter("S"):
            logging.debug("S paramter missing")
            return        
        target = g.get_float_by_letter("S", 0.0)

        if g.has_letter("P") or g.has_letter("T"):
            if g.has_letter("P"):  # Set hotend temp based on the P-param
                heater_index = g.get_int_by_letter("P", 0)
            elif g.has_letter("T"):  # Set hotend temp based on the T-param
                heater_index = g.get_int_by_letter("T", 0)
            if heater_index > len(self.printer.heaters)-1:
                logging.warning("M104: heater index out of bounds: {}".format(heater_index))
                return
            heater_name = "EHABC"[heater_index]
        else:  # Change hotend temperature based on the chosen tool
            target = float(g.token_value(0))
            heater_name = self.printer.current_tool

        heater = self.printer.heaters[heater_name]
        logging.debug("setting temp for {} to {}".format(heater.name, target))    
        heater.set_target_temperature(target)

    def get_description(self):
        return "Set extruder temperature"

    def get_long_description(self):
        return ("Set extruder temperature. "
                "Use either T<index> or P<index> "
                "to choose heater, use S for the target temp")

    def is_buffered(self):
        return True
