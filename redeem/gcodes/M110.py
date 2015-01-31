"""
GCode M110
Reset line counter

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

    def execute(self, g):
        Gcode.line_number = 0

    def get_description(self):
        return "Reset GCode line counter"

    def is_buffered(self):
        return True
