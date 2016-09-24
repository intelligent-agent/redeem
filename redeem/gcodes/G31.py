"""
GCode G31
Dock sled

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

class G31(GCodeCommand):

    def execute(self, g):
        gcodes = self.printer.config.get("Macros", "G31").split("\n")
        self.printer.path_planner.wait_until_done()
        for gcode in gcodes:        
            G = Gcode({"message": gcode, "prot": g.prot})
            self.printer.processor.execute(G)
            self.printer.path_planner.wait_until_done()

    def get_description(self):
        return "Dock sled"

    def get_long_description(self):
        return ("Dock sled. This is a macro G-code, so it will read all "
                "gcodes that has been defined for it. "
                "It is intended to remove or disable the Z-probing "
                "mechanism, either by physically removing it as is "
                "the case of a servo controlled device, or by disabling "
                "power to a probe or simply disabling the switch as an end stop")

    def is_buffered(self):
        return True

    def get_test_gcodes(self):
        return ["G31"]

