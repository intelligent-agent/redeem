"""
GCode G2 and G3
Circular movement

Author: Elias Bakken
"""

from GCodeCommand import GCodeCommand
try:
    from Path import Path, RelativePath, AbsolutePath
except ImportError:
    from redeem.Path import Path, RelativePath, AbsolutePath

import logging


class G2(GCodeCommand):

    def execute_common(self, g):
        if g.has_letter("F"):  # Get the feed rate & convert from mm/min to SI unit m/s
            self.printer.feed_rate = g.get_distance_by_letter("F") / 60000.
            g.remove_token_by_letter("F")

        if g.has_letter("Q"):  # Get the acceration & convert from mm/min^2 to SI unit m/s^2
            self.printer.accel = g.get_distance_by_letter("Q") / 3600000.
            g.remove_token_by_letter("Q")

        smds = {}
        for i in range(g.num_tokens()):
            axis = g.token_letter(i)
            # Get the value, new position or vector
            value =  float(g.token_value(i)) / 1000.0
            if axis in ('E', 'H') and self.printer.extrude_factor != 1.0:
                   value *= self.printer.extrude_factor
            smds[axis] = value        

        if self.printer.movement == Path.ABSOLUTE:
            path = AbsolutePath(smds, self.printer.feed_rate * self.printer.factor, self.printer.accel)
        elif self.printer.movement == Path.RELATIVE:
            path = RelativePath(smds, self.printer.feed_rate * self.printer.factor, self.printer.accel)
        else:
            logging.error("invalid movement: " + str(self.printer.movement))
            return

        # http://www.manufacturinget.org/2011/12/cnc-g-code-g02-and-g03/
        if g.has_letter('R'):
            path.R = float(g.get_value_by_letter("R")) / 1000.0
            return path

        if self.printer.arc_plane in [Path.X_Y_ARC_PLANE, Path.X_Z_ARC_PLANE]:
            path.I = float(g.get_value_by_letter("I"))/1000.0 if g.has_letter("I") else 0.0

        if self.printer.arc_plane in [Path.X_Y_ARC_PLANE, Path.Y_Z_ARC_PLANE]:
            path.J = float(g.get_value_by_letter("J"))/1000.0 if g.has_letter("J") else 0.0

        if self.printer.arc_plane in [Path.X_Z_ARC_PLANE, Path.Y_Z_ARC_PLANE]:
            path.K = float(g.get_value_by_letter("K")) / 1000.0 if g.has_letter("K") else 0.0

        return path

    def execute(self, g):
        path = self.execute_common(g)
        path.movement = Path.G2

        # Add the path. This blocks until the path planner has capacity
        self.printer.path_planner.add_path(path)
   
    def get_description(self):
        return ("Clockwise arc")

    def is_buffered(self):
        return True

    def get_test_gcodes(self):
        return [
            "G17",
            "G1 Y10",
            "G2 X12.803 Y15.303 I7.50"
        ]


# alias for G2, since some CAD/CAM generate with leading zero
class G02(G2):
    pass

class G3(G2):
    def execute(self, g):
        path = self.execute_common(g)
        path.movement = Path.G3

        # Add the path. This blocks until the path planner has capacity
        self.printer.path_planner.add_path(path)


    def get_description(self):
        return ("Counter-clockwise arc")


# alias for G3, since some CAD/CAM generate with leading zero
class G03(G3):
    pass
