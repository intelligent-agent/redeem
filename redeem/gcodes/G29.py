"""
GCode G29
Probe bed

Author: Elias Bakken
email: elias(dot)bakken(at)gmail dot com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import logging
try:
    from Gcode import Gcode
    from Path import Path
except ImportError:
    from redeem.Gcode import Gcode
    from redeem.Path import Path

class G29(GCodeCommand):

    def execute(self, g):

        gcodes = self.printer.config.get("Macros", "G29").split("\n")
        self.printer.path_planner.wait_until_done()
        for gcode in gcodes:        
            G = Gcode({"message": gcode, "prot": g.prot})
            self.printer.processor.execute(G)
            self.printer.path_planner.wait_until_done()

        # Remove the offset from the probed points        
        self.printer.probe_heights -= min(self.printer.probe_heights)

        # Log the found heights
        for k, v in enumerate(self.printer.probe_points):
            self.printer.probe_points[k]["Z"] = self.printer.probe_heights[k]
        logging.info("Found heights: ")
        logging.info(self.printer.probe_points)

        # Update the bed compensation matrix
        Path.update_autolevel_matrix(self.printer.probe_points, self.printer.probe_heights)


    def get_description(self):
        return "Probe the bed at three points"

    def get_long_description(self):
        return "Probe the bed at specified points and update the bed compensation matrix based on the found points."

    def is_buffered(self):
        return True

    def get_test_gcodes(self):
        return ["G29"]

