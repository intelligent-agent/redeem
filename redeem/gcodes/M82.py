"""
GCode M82
Set the extruder mode to absoute

Author: Elias Bakken
email: elias(at)iagent(dot)no
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

from .GCodeCommand import GCodeCommand
from redeem.Path import Path


class M82(GCodeCommand):

    def execute(self, g):

        for axis in "EHABC":
            if axis not in self.printer.axes_absolute:
                self.printer.axes_absolute.append(axis)
            if axis in self.printer.axes_relative:
                self.printer.axes_relative.remove(axis)

        if self.printer.axes_relative == []:
            self.printer.movement = Path.ABSOLUTE
        else:
            self.printer.movement = Path.MIXED

    def get_description(self):
        return "Set the extruder mode to absolute"

    def get_long_description(self):
        return "Makes the extruder interpret extrusion as absolute positions. This is the default in Redeem."

    def is_buffered(self):
                return True
