"""
GCode M130 M131 and M132
Adjust PID settings

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand


class M130(GCodeCommand):

    def execute(self, g):
        extr = g.get_int_by_letter("P", 0)
        value = float(g.get_value_by_letter("S"))
        if extr == 0:
            self.printer.heaters['E'].P = value
        elif extr == 1:
            self.printer.heaters['H'].P = value
        elif extr == 2:
            self.printer.heaters['HBP'].P = value

    def get_description(self):
        return "Set PID P-value, Format (M130 P0 S8.0)"


class M131(GCodeCommand):

    def execute(self, g):
        extr = g.get_int_by_letter("P", 0)
        value = float(g.get_value_by_letter("S"))
        if extr == 0:
            self.printer.heaters['E'].I = value
        elif extr == 1:
            self.printer.heaters['H'].I = value
        elif extr == 2:
            self.printer.heaters['HBP'].I = value

    def get_description(self):
        return "Set PID I-value, Format (M131 P0 S8.0)"


class M132(GCodeCommand):

    def execute(self, g):
        extr = g.get_int_by_letter("P", 0)
        value = float(g.get_value_by_letter("S"))
        if extr == 0:
            self.printer.heaters['E'].D = value
        elif extr == 1:
            self.printer.heaters['H'].D = value
        elif extr == 2:
            self.printer.heaters['HBP'].D = value

    def get_description(self):
        return "Set PID D-value, Format (M132 P0 S8.0)"
