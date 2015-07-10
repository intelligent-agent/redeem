"""
GCode G32
Undock sled

Author: Elias Bakken
email: elias(dot)bakken(at)gmail dot com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import logging
try:
    from Gcode import Gcode
except ImportError:
    from redeem.Gcode import Gcode

class G32(GCodeCommand):

    def execute(self, g):
        gcodes = self.printer.config.get("Macros", "G32").split("\n")
        self.printer.path_planner.wait_until_done()
        for gcode in gcodes:        
            G = Gcode({"message": gcode, "prot": g.prot})
            self.printer.processor.execute(G)
            self.printer.path_planner.wait_until_done()

    def get_description(self):
        return "Undock sled"

    def is_buffered(self):
        return True

    def get_test_gcodes(self):
        return ["G32"]

