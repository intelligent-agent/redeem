'''
GCode G92
Set current position of steppers without moving them

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

from GCodeCommand import GCodeCommand
import logging
from Path import Path

class G92(GCodeCommand):

    def execute(self,g):
        if g.num_tokens() == 0:
            logging.debug("Adding all to G92")
            g.set_tokens(["X0", "Y0", "Z0", "E0", "H0"])            # If no token is present, do this for all
        pos = {}                                                    # All steppers 
        for i in range(g.num_tokens()):                             # Run through all tokens
            axis = g.token_letter(i)                                # Get the axis, X, Y, Z or E
            pos[axis] = float(g.token_value(i))/1000.0              # Get the value, new position or vector             
        if self.printer.current_tool == "H" and "E" in pos: 
            logging.debug("Adding H to G92")
            pos["H"] = pos["E"];
            del pos["E"]
        path = Path(pos, self.printer.feed_rate, "G92")                     # Make a path segment from the axes
        self.printer.path_planner.add_path(path)  


    def get_description(self):
        return "Set the current position of steppers without moving them"
