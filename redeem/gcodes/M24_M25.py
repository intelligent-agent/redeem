"""
GCode M24 and M25
Resume / Pause print

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand


class M24(GCodeCommand):

    def execute(self, g):
        self.printer.path_planner.resume()

    def get_description(self):
        return "Resume the print where it was paused by the M25 command."

    def is_buffered(self):
        return False


class M25(GCodeCommand):

    def execute(self, g):
        self.printer.path_planner.suspend()

    def get_description(self):
        return "Pause the current print."

    def is_buffered(self):
        return False
