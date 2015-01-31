"""
GCode G92
Set current position of steppers without moving them

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import logging
try:
    from Path import G92Path
except ImportError:
    from redeem.Path import G92Path

class G92(GCodeCommand):

    def execute(self, g):
        if g.num_tokens() == 0:
            # If no token is present, do this for all steppers
            logging.debug("Adding all to G92")
            g.set_tokens(["X0", "Y0", "Z0", "E0", "H0"])
        pos = {}
        for i in range(g.num_tokens()):
            axis = g.token_letter(i)  # Get the axis, X, Y, Z or E
            # Get the value, new position or vector
            pos[axis] = float(g.token_value(i)) / 1000.0

        # Make a path segment from the axes
        path = G92Path(pos, self.printer.feed_rate)
        self.printer.path_planner.add_path(path)

    def get_description(self):
        return "Set the current position of steppers without moving them"

    def is_buffered(self):
        return True

    def get_test_gcodes(self):
        return ["G92"]

