"""
GCode M83
Set the extruder mode to relative

Author: Elias Bakken
email: elias(at)iagent(dot)no
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import os
try:
    from Printer import Printer
    from Path import Path
except ImportError:
    from redeem.Printer import Printer
    from redeem.Path import Path

class M83(GCodeCommand):

    def execute(self, g):
        self.printer.movement = Path.MIXED
        for axis in "EHABC":
            if axis not in self.printer.axes_relative:
                self.printer.axes_relative.append(axis)
            if axis in self.printer.axes_absolute:
                self.printer.axes_absolute.remove(axis)
        #If all axes are relative now, change to absolute mode
        if self.printer.axes_absolute == []:
            self.printer.movement = Path.RELATIVE

    def get_description(self):
        return "Set the extruder mode to relative"

    def get_long_description(self):
        return "Makes the extruder interpret extrusion values as relative positions."

