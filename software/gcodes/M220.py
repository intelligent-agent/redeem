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
	if g.has_letter("S"):
            self.printer.factor = float(g.get_value_by_letter("S")) / 100
        else:
            self.printer.factor = 1

	logging.debug("M220 factor " + str(self.printer.factor))
	
    def get_description(self):
        return "M220 S<factor in percent> - set speed factor override percentage"

    def is_buffered(self):
        return False

