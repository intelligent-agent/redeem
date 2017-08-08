"""
GCode M220
set speed factor override percentage :

Author: Boris Lasic
email: boris(at)max(dot)si
Website: http://www.max.si
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import logging

class M220(GCodeCommand):

    def execute(self, g):
        self.printer.speed_factor = g.get_float_by_letter("S", 100) / 100
	logging.debug("M220 speed factor " + str(self.printer.speed_factor))
	
    def get_description(self):
        return "Set speed override percentage"

    def get_long_description(self):
        return "M220 S<speed factor in percent> - set speed factor override percentage"

    def is_buffered(self):
        return False

