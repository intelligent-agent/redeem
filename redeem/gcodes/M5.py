"""
GCode M5
Spindle off

Author: Elias Bakken
email: elias(dot)bakken(at)gmail dot com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

from .GCodeCommand import GCodeCommand
from redeem.Gcode import Gcode


class M5(GCodeCommand):

    def execute(self, g):
        gcodes = self.printer.config.get("Macros", "M5").split("\n")
        self.printer.path_planner.wait_until_done()
        for gcode in gcodes:        
            G = Gcode({"message": gcode, "parent": g})
            self.printer.processor.execute(G)
            self.printer.path_planner.wait_until_done()

    def get_description(self):
        return "Spindle off"

    def get_long_description(self):
        return ("Spindle off")

    def is_buffered(self):
        return True

    def get_test_gcodes(self):
        return ["M5"]

