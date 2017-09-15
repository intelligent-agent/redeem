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
    from Path import Path, RelativePath, AbsolutePath, MixedPath
except ImportError:
    from redeem.Path import Path, RelativePath, AbsolutePath, MixedPath

import logging


class G0(GCodeCommand):

    def execute(self, g):
        if g.has_letter("F"):  # Get the feed rate & convert from mm/min to SI unit m/s
            self.printer.feed_rate = g.get_distance_by_letter("F") / 60000.
            g.remove_token_by_letter("F")
        if  g.has_letter("Q"):  # Get the Accel & convert from mm/min^2 to SI unit m/s^2
            self.printer.accel = g.get_distance_by_letter("Q") / 3600000.
            g.remove_token_by_letter("Q")
        smds = {}
        for i in range(g.num_tokens()):
            axis = self.printer.movement_axis(g.token_letter(i))

            # Get the value, new position or vector
            value = float(g.token_distance(i)) / 1000.0 # mm to SI unit m
            if axis in ('E', 'H', 'A', 'B', 'C'):
                value *= self.printer.extrude_factor
            smds[axis] = value
    
        if self.printer.movement == Path.ABSOLUTE:
            path = AbsolutePath(smds, self.printer.feed_rate * self.printer.speed_factor, self.printer.accel)
        elif self.printer.movement == Path.RELATIVE:
            path = RelativePath(smds, self.printer.feed_rate * self.printer.speed_factor, self.printer.accel)
        elif self.printer.movement == Path.MIXED:
            path = MixedPath(smds, self.printer.feed_rate * self.printer.speed_factor, self.printer.accel)
        else:
            logging.error("invalid movement: " + str(self.printer.movement))
            return
        
        # Add the path. This blocks until the path planner has capacity
        self.printer.path_planner.add_path(path)

    def get_description(self):
        return "Control the printer head position as well as the currently " \
               "selected tool."

    def get_long_description(self):
        return ("Move each axis by the amount and direction depicted.\n"
                "X = X-axis (mm)\n"
                "Y = Y-axis (mm)\n"
                "Z = Z-axis (mm)\n"
                "E = E-axis (mm)\n"
                "H = H-axis (mm)\n"
                "A = A-axis (mm) - only if axis present\n"
                "B = B-axis (mm) - only if axis present\n"
                "C = C-axis (mm) - only if axis present\n"
                "F = move speed (mm/min) - stored until daemon reset\n"
                "Q = move acceleration (mm/min^2) - stored until daemon reset\n")

    def is_buffered(self):
        return True

    def get_test_gcodes(self):
        return [
            "G0 X0 Y0 Z0 F1000", 
            "G0 X1 Y1 Z0"
        ]


class G1(G0):
    pass

