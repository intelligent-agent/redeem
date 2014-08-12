"""
GCode G21
Setting units

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand


class G21(GCodeCommand):

    def execute(self,g):
        #FIXME: This is not used anywhere.
        self.printer.factor = 1.0

    def get_description(self):
        return "Set units to millimeters"
