"""
GCode G29
This is a macro function followed by saving the new bed matrix

Author: Elias Bakken
email: elias(dot)bakken(at)gmail dot com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import logging
import json
        
try:
    from Gcode import Gcode
    from Path import Path
    from Alarm import Alarm
    from BedCompensation import BedCompensation
except ImportError:
    from redeem.Gcode import Gcode
    from redeem.Path import Path
    from redeem.Alarm import Alarm
    from redeem.BedCompensation import BedCompensation

class G29(GCodeCommand):

    def execute(self, g):

        gcodes = self.printer.config.get("Macros", "G29").split("\n")
        self.printer.path_planner.wait_until_done()
        for gcode in gcodes:        
            G = Gcode({"message": gcode, "prot": g.prot})
            self.printer.processor.execute(G)
            self.printer.path_planner.wait_until_done()
            
        

        # Remove the offset from the probed points        
        if self.printer.probe_points[0]["X"] == 0 and self.printer.probe_points[0]["Y"] == 0:
             min_value = self.printer.probe_heights[0]
        else:
            min_value = min(self.printer.probe_heights)
        
        for i in range(len(self.printer.probe_heights)):
            self.printer.probe_heights[i] -= min_value

        # Log the found heights
        for k, v in enumerate(self.printer.probe_points):
            self.printer.probe_points[k]["Z"] = self.printer.probe_heights[k]
        logging.info("Found heights: "+str(self.printer.probe_points))

        # Add 'S'=simulate To not update the bed matrix.  
        if not g.has_letter("S"):
            # Update the bed compensation matrix
            self.printer.path_planner.update_autolevel_matrix(self.printer.probe_points, self.printer.probe_heights)
            logging.info("Updated bed compensation matrix: \n"+str(self.printer.matrix_bed_comp))
        else:
            # Update probe points to make comparable with update
            BedCompensation.create_rotation_matrix(self.printer.probe_points, self.printer.probe_heights)

        Alarm.action_command("bed_probe_data", json.dumps(self.printer.probe_points))

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

