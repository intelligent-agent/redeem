"""
GCode G90 and G91
Set movement mode to absolute or relative

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

from .GCodeCommand import GCodeCommand
from redeem.Path import Path


class G90(GCodeCommand):

    def execute(self, g):
        self.printer.axes_absolute = ["X", "Y", "Z", "E", "H", "A", "B", "C"]
        self.printer.axes_relative = []
        self.printer.movement = Path.ABSOLUTE

    def get_description(self):
        return "Set movement mode to absolute"

    def is_buffered(self):
        return True

    def is_async(self):
        return True


class G91(GCodeCommand):

    def execute(self, g):
        self.printer.axes_absolute = []
        self.printer.axes_relative = ["X", "Y", "Z", "E", "H", "A", "B", "C"]
        self.printer.movement = Path.RELATIVE

    def get_description(self):
        return "Set movement mode to relative"

    def is_buffered(self):
        return True

    def is_async(self):
        return True
