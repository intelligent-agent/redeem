"""
GCode M106 and M107
Control fans

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

from .GCodeCommand import GCodeCommand


class M106(GCodeCommand):

    def execute(self, gcode):
        # Get the value, 255 if not present
        value = float(gcode.get_float_by_letter("S", 255)) / 255.0
        
        fan_controller = None
        if gcode.has_letter("P"):
            fan_no = gcode.get_int_by_letter("P", 0)
            if fan_no < len(self.printer.fans):
                fan_controller = self.printer.fans[fan_no].input
        else:
            fan_controller = self.printer.command_connect["M106"]
        
    
        if gcode.has_letter("R"): # Ramp to value
            delay = gcode.get_float_by_letter("R", 0.01)
            fan_controller.ramp_to(value, delay)            
        else:
            fan_controller.set_target_value(value)

    def get_description(self):
        return "Set fan power."

    def get_long_description(self):
        return "Set the current fan power. Specify S parameter for the " \
               "power (between 0 and 255) and the P parameter for the fan " \
               "number. P=0 and S=255 by default. If no P, use fan from config. "\
               "If no fan configured, use fan 0. If 'R' is present, ramp to the value"

    def is_buffered(self):
        return True


class M107(GCodeCommand):

    def execute(self, gcode):
        fan_controller = None
        if gcode.has_letter("P"):
            fan_no = gcode.get_int_by_letter("P", 0)
            if fan_no < len(self.printer.fans):
                fan_controller = self.printer.fans[fan_no].input
        else:
            fan_controller = self.printer.command_connect["M107"]
            
        fan_controller.set_target_value(0.0)

    def get_description(self):
        return "set fan off"

    def get_long_description(self):
        return "Set the current fan off. Specify P parameter for the fan " \
               "number. If no P, use fan from config. "\
               "If no fan configured, use fan 0"

    def is_buffered(self):
        return True
