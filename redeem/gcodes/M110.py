"""
GCode M110
Set current Gcode line number

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
try:
    from Gcode import Gcode
except ImportError:
    from redeem.Gcode import Gcode

class M110(GCodeCommand):
    def execute(self, gcode):
        if gcode.has_letter("N"):  # Line number is specified
            Gcode.line_number = gcode.get_int_by_letter("N",0)
        else:  # No line number specified, reset the counter
            Gcode.line_number = 0

    def get_description(self):
        return "Set current gcode line number"

    def is_buffered(self):
        return True
