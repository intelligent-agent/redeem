"""
GCode G21
Setting units

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import logging

class G20(GCodeCommand):

    def execute(self,g):
        self.printer.factor = 25.4
        logging.debug("Set units to inches")

    def get_description(self):
        return "Set units to inches"

class G21(GCodeCommand):

    def execute(self,g):
        self.printer.factor = 1.0
        logging.debug("Set units to millimeters")

    def get_description(self):
        return "Set units to millimeters"
