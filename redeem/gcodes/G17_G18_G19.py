"""
GCode G17, G18 and G19
Set arc plane

Author: Andrew Mirsky
email: andrew(at)mirskytech(dot)com
Website: http://mirskytech.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
try:
    from Path import Path
except ImportError:
    from redeem.Path import Path


class G17(GCodeCommand):

    def execute(self, g):
        self.printer.path_planner.wait_until_done()
        self.printer.arc_plane = Path.X_Y_ARC_PLANE

    def get_description(self):
        return "Set arc plane to X / Y"

    def is_buffered(self):
        return True


class G18(GCodeCommand):

    def execute(self, g):
        self.printer.path_planner.wait_until_done()
        self.printer.arc_plane = Path.X_Z_ARC_PLANE

    def get_description(self):
        return "Set arc plane to X / Z"

    def is_buffered(self):
        return True


class G19(GCodeCommand):

    def execute(self, g):
        self.printer.path_planner.wait_until_done()
        self.printer.arc_plane = Path.Y_Z_ARC_PLANE

    def get_description(self):
        return "Set arc plane to Y / Z"

    def is_buffered(self):
        return True
