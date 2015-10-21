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

        logging.debug(self.printer.probe_heights)

        # Add 'S'=simulate To not update the bed matrix.  
        if not g.has_letter("S"):
            # Remove the offset from the probed points        
            if self.printer.probe_points[0]["X"] == 0 and self.printer.probe_points[0]["Y"] == 0:
                # If the origin is located in the first probe point, remove that. 
                self.printer.probe_heights -= self.printer.probe_heights[0]
            else:
                # Else, remove the lowest. 
                self.printer.probe_heights -= min(self.printer.probe_heights)

            # Log the found heights
            for k, v in enumerate(self.printer.probe_points):
                self.printer.probe_points[k]["Z"] = self.printer.probe_heights[k]
            logging.info("Found heights: ")
            logging.info(self.printer.probe_points)


            # Update the bed compensation matrix
            Path.update_autolevel_matrix(self.printer.probe_points, self.printer.probe_heights)
            logging.debug("New Bed level matrix: ")
            logging.debug(Path.matrix_bed_comp)


    def get_description(self):
        return "Probe the bed at specified points"

    def get_long_description(self):
        return ("Probe the bed at specified points and "
                "update the bed compensation matrix based "
                "on the found points. Add 'S' to NOT update the bed matrix.")

    def is_buffered(self):
        return True

    def get_test_gcodes(self):
        return ["G29"]

