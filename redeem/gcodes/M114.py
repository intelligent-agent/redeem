"""
GCode M114
Get current printer head position

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand


class M114(GCodeCommand):
    def execute(self, g):
        pos = self.printer.path_planner.get_current_pos(mm=True)
        axis_order = ['X', 'Y', 'Z', 'E']
        pos_ordered = [(i, pos[i]) for i in axis_order if i in pos]
        pos_ordered.extend(sorted(i for i in pos.iteritems() if i[0] not in axis_order))
        g.set_answer("ok C: " + ' '.join('%s:%.1f' % (i[0], i[1]) for i in pos_ordered))

    def get_description(self):
        return "Get current printer head position"

    def get_long_description(self):
        return ("Get current printer head position. "
            "The returned value is in millimeters.")

    def get_test_gcodes(self):
        return ["M114"]

