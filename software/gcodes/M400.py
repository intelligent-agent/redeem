'''
GCode M400
Wait until all buffered paths are executed

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

from GCodeCommand import GCodeCommand


class M400(GCodeCommand):

    def execute(self, g):
        self.printer.path_planner.wait_until_done()

    def get_description(self):
        return "Wait until all buffered paths are executed"
