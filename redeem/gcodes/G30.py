"""
GCode G30
Single Z probe

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
    

class G30(GCodeCommand):

    def execute(self, g):
        if g.has_letter("P"): # Load point
            index = int(g.get_value_by_letter("P"))
            point = self.printer.probe_points[index]
        else:
            # If no porobe point is specified, use current pos
            point = self.printer.path_planner.get_current_pos()
        if g.has_letter("X"): # Override X
            point["X"] = float(g.get_value_by_letter("X"))
        if g.has_letter("Y"): # Override Y
            point["Y"] = float(g.get_value_by_letter("Y"))

        G0 = Gcode({"message": "G0 X{} Y{}".format(point["X"], point["Y"]), "prot": g.prot})    
        self.printer.processor.execute(G0)
        self.printer.path_planner.wait_until_done()
        height = self.printer.path_planner.probe(0.01) # Probe one cm
        logging.info("Found Z probe height {} at (X, Y) = ({}, {})".format(height, point["X"], point["Y"]))
        if g.has_letter("S"):
            if not g.has_letter("P"):
                logging.warning("G30: S-parameter was set, but no index (P) was set.")
            else:
                self.printer.probe_heights[index] = height
                self.printer.send_message(g.prot, 
                    "Found Z probe height {} at (X, Y) = ({}, {})".format(height, point["X"], point["Y"]))
        

    def get_description(self):
        return "Probe the bed at current point"

    def is_buffered(self):
        return True

    def get_test_gcodes(self):
        return ["G30", "G30 P0", "G30 P1 X10 Y10"]

