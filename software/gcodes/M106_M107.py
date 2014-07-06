'''
GCode M106 and M107
Control fans

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

from GCodeCommand import GCodeCommand


class M106(GCodeCommand):

    def execute(self, gcode):
        fan_no = gcode.get_int_by_letter("P", 0)               
        value = float(gcode.get_int_by_letter("S", 255))/255.0
        fan = self.printer.fans[fan_no]
        fan.set_value(value)

    def get_description(self):
        return "Set the current fan power. Specify S parameter for the power (between 0 and 255) and the P parameter for the fan number. P=0 and S=255 by default."

    def is_buffered(self):
        return True

class M107(GCodeCommand):

    def execute(self, gcode):
        fan_no = gcode.get_int_by_letter("P", 0)               
        fan = self.printer.fans[fan_no]
        fan.set_value(0)

    def get_description(self):
        return "Turn off the specified fan. Specify the P parameter for the fan number. P=0 by default."

    def is_buffered(self):
        return True
