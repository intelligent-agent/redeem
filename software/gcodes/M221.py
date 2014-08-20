"""
GCode M221
set extrude factor override percentage 

Author: Boris Lasic
email: boris(at)max(dot)si
Website: http://www.max.si
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand


class M221(GCodeCommand):

    def execute(self, g):
	if g.has_letter("S"):
            self.printer.extrude_factor = float(g.get_value_by_letter("S")) / 100
        else:
            self.printer.extrude_factor = 1.0


    def get_description(self):
        return "M221 S<factor in percent> - set extrude factor override percentage"

    def is_buffered(self):
        return True

