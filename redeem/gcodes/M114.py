"""
GCode M114
Get current printer head position

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
from six import iteritems


class M114(GCodeCommand):
    def execute(self, g):
        if g.has_letter("M"):
            pos = self.printer.path_planner.get_current_pos(mm=True, ideal=False)
        else:
            pos = self.printer.path_planner.get_current_pos(mm=True, ideal=True)            
        axis_order = ['X', 'Y', 'Z', 'E']
        pos_ordered = [(i, pos[i]) for i in axis_order if i in pos]
        pos_ordered.extend(sorted(i for i in iteritems(pos) if i[0] not in axis_order))
        g.set_answer("ok C: " + ' '.join('%s:%.1f' % (i[0], i[1]) for i in pos_ordered))

    def get_description(self):
        return "Get current printer head position"

    def get_long_description(self):
        return ("Get current printer head position. "
            "This is the ideal positition, without bed compensation. "
            "The returned value is in millimeters.\n"
            "M = Return the position seen with the bed matix enabled " )

    def get_test_gcodes(self):
        return ["M114"]

