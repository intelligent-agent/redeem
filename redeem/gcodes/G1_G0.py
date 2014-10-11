"""
GCode G0 and G1
Controlling printer head position

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
try:
    from Path import Path, RelativePath, AbsolutePath
except ImportError:
    from redeem.Path import Path, RelativePath, AbsolutePath

import logging


class G0(GCodeCommand):

    def execute(self, g):
        if g.has_letter("F"):  # Get the feed rate
            # Convert from mm/min to SI unit m/s
            self.printer.feed_rate = float(g.get_value_by_letter("F"))
            self.printer.feed_rate /= 60000.0
            g.remove_token_by_letter("F")
        smds = {}
        for i in range(g.num_tokens()):
            axis = g.token_letter(i)
	    # Get the value, new position or vector
	    value =  float(g.token_value(i)) / 1000.0
	    if (axis == 'E' or axis == 'H') and self.printer.extrude_factor != 1.0:
               value *= self.printer.extrude_factor
            smds[axis] = value

        if self.printer.movement == Path.ABSOLUTE:
            path = AbsolutePath(smds, self.printer.feed_rate * self.printer.factor)
        elif self.printer.movement == Path.RELATIVE:
            path = RelativePath(smds, self.printer.feed_rate * self.printer.factor)
        else:
            logging.error("invalid movement: " + str(self.printer.movement))
            return
    
        # Add the path. This blocks until the path planner has capacity
        self.printer.path_planner.add_path(path)

    def get_description(self):
        return "Control the printer head position as well as the currently " \
               "selected tool."

    def is_buffered(self):
        return True

    def get_test_gcodes(self):
        return [
            "G0 X0 Y0 Z0 F1000", 
            "G0 X1 Y1 Z0"
        ]

class G1(G0):
    pass

