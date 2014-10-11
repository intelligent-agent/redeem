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
        g.set_answer("ok C: " + ' '.join('%s:%s' % i for i in self.printer
                     .path_planner.get_current_pos().iteritems()))

    def get_description(self):
        return "Get current printer head position"

    def get_test_gcodes(self):
        return ["M114"]

