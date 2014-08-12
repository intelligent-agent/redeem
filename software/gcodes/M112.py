"""
GCode M112
Emergency stop

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand


class M112(GCodeCommand):

    def execute(self, g):
        self.printer.path_planner.emergency_interrupt()

    def get_description(self):
        return "Cancel all the planned move in emergency."

    def is_buffered(self):
        return False
