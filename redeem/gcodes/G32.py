"""
GCode G32
Probe bed at three points and calculate the Z-plane

Author: Elias Bakken
email: elias(dot)bakken(at)gmail dot com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import logging
try:
    from Gcode import Gcode
    from Path import Path, RelativePath, AbsolutePath
except ImportError:
    from redeem.Gcode import Gcode
    from redeem.Path import Path, RelativePath, AbsolutePath

class G32(GCodeCommand):

    def execute(self, g):
        G = Gcode({"message": "G29", "prot": g.prot})
        self.printer.processor.execute(G)
        self.printer.path_planner.wait_until_done()
        # Key, the bed is now probed at three  points and the 
        # Found values should be stored in the printer class. 
        Path.update_autolevel_matrix(self.printer.probe_points, self.printer.probe_heights)

    def get_description(self):
        return "Probe the bed at three points and calculate the Z-plane"

    def is_buffered(self):
        return True

    def get_test_gcodes(self):
        return ["G32"]

