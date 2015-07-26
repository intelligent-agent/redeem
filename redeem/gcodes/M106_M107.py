"""
GCode M106 and M107
Control fans

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand


class M106(GCodeCommand):

    def execute(self, gcode):
        fans = []
        if gcode.has_letter("P"):
            fan_no = gcode.get_int_by_letter("P", 0)
            if fan_no < len(self.printer.fans):
                fans.append(self.printer.fans[fan_no])
        elif len(self.printer.controlled_fans) > 0 : # No P in gcode, use fans from settings file
            fans = self.printer.controlled_fans
        else: # Uee fan 0
            fans.append(self.printer.fans[0])

        # Get the value, 255 if not present
        value = float(gcode.get_int_by_letter("S", 255)) / 255.0
    
        for fan in fans:
            if gcode.has_letter("R"): # Ramp to value
                delay = gcode.get_float_by_letter("R", 0.01)
                fan.ramp_to(value, delay)            
            else:
                fan.set_value(value)

    def get_description(self):
        return "Set the current fan power. Specify S parameter for the " \
               "power (between 0 and 255) and the P parameter for the fan " \
               "number. P=0 and S=255 by default. If no P, use fan from config. "\
               "If no fan configured, use fan 0. If 'R' is present, ramp to the value"

    def is_buffered(self):
        return True


class M107(GCodeCommand):

    def execute(self, gcode):
        fans = []
        if gcode.has_letter("P"):
            fan_no = gcode.get_int_by_letter("P", 0)
            if fan_no < len(self.printer.fans):
                fans.append(self.printer.fans[fan_no])
        elif len(self.printer.controlled_fans) > 0 : # No P in gcode, use fans from settings file
            fans = self.printer.controlled_fans
        else: # Uee fan 0
            fans.append(self.printer.fans[0])

        for fan in fans:
            fan.set_value(0)

    def get_description(self):
        return "Set the current fan off. Specify P parameter for the fan " \
               "number. If no P, use fan from config. "\
               "If no fan configured, use fan 0"

    def is_buffered(self):
        return True
