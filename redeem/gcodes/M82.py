"""
GCode M82
Set the extruder mode to absoute

Author: Elias Bakken
email: elias(at)iagent(dot)no
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
try:
    from Printer import Printer
    from Path import Path
except ImportError:
    from redeem.Printer import Printer
    from redeem.Path import Path

class M82(GCodeCommand):

    def execute(self, g):
        self.printer.movement = Path.MIXED
        for axis in "EHABC":
            if axis not in self.printer.axes_absolute:
                self.printer.axes_absolute.append(axis)
            if axis in self.printer.axes_relative:
                self.printer.axes_relative.remove(axis)
        #If all axes are absolute now, change to absolute mode
        if self.printer.axes_relative == []:
            self.printer.movement = Path.ABSOLUTE

    def get_description(self):
        return "Set the extruder mode to absolute"

    def get_long_description(self):
        return "Makes the extruder interpret extrusion as absolute positions. This is the default in Redeem."

