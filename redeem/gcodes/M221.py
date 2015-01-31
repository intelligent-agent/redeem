"""
GCode M221
set extrude factor override percentage 

Author: Boris Lasic
email: boris(at)max(dot)si
Website: http://www.max.si
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
try:
    from Path import Path, G92Path
except ImportError:
    from redeem.Path import Path, G92Path


class M221(GCodeCommand):

    def execute(self, g):

	# restore previous position of E an H axis
	if self.printer.movement == Path.ABSOLUTE:
            pos = self.printer.path_planner.get_current_pos()
	    pos['E'] /= self.printer.extrude_factor
	    pos['H'] /= self.printer.extrude_factor
            self.printer.path_planner.add_path(G92Path(pos, self.printer.feed_rate)) 		

	# apply new extrude factor
	if g.has_letter("S"):
            self.printer.extrude_factor = float(g.get_value_by_letter("S")) / 100
        else:
            self.printer.extrude_factor = 1.0

	# set E and H to new Positions
	if self.printer.movement == Path.ABSOLUTE:
            pos = self.printer.path_planner.get_current_pos()
	    pos['E'] *= self.printer.extrude_factor
	    pos['H'] *= self.printer.extrude_factor
            self.printer.path_planner.add_path(G92Path(pos, self.printer.feed_rate))

	    
    def get_description(self):
        return "M221 S<factor in percent> - set extrude factor override percentage"

    def is_buffered(self):
        return False
