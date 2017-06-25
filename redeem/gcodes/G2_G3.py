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
        arc_plane = [] # XY, XZ, or YZ -- in any order. A third X|Y|Z if any becomes the axis_linear for "helical" moves
        arc_linear = None
        for i in range(g.num_tokens()):
            axis = g.token_letter(i)
            plane_axis = self.printer.AXES[:3].find(axis) # X, Y or Z?
            if plane_axis >= 0:
                if len(arc_plane) < 2: 
                    arc_plane.append(plane_axis)
                else:
                    arc_linear = plane_axis 
            
	    # Get the value, new position or vector
	    value =  float(g.token_distance(i)) / 1000.0
            if axis in "EH":
               value *= self.printer.extrude_factor

            smds[axis] = value

        if self.printer.movement == Path.ABSOLUTE:
            path = AbsolutePath(smds, self.printer.feed_rate * self.printer.factor, self.printer.accel)
        elif self.printer.movement == Path.RELATIVE:
            path = RelativePath(smds, self.printer.feed_rate * self.printer.factor, self.printer.accel)
        else:
            logging.error("invalid movement: " + str(self.printer.movement))
            # TODO: fix this        

        path.set_arc_plane(arc_plane[0], arc_plane[1])
        path.set_arc_linear(arc_linear) 

        return path        

    def execute(self, g):
        path = self.execute_common(g)
        path.movement = Path.G2

        # Add the path. This blocks until the path planner has capacity
        self.printer.path_planner.add_path(path)
   
    def get_description(self):
        return ("Clockwise arc (experimental, not tested) "
               "")

    def is_buffered(self):
        return True

    def get_test_gcodes(self):
        return [
            "G90",
            "G1 X10 Y60",
            "G2 X60 Y10 I50",
            "G3 X10 Y60 J50"
        ]

class G3(G2):
    def execute(self, g):
        path = self.execute_common(g)
        path.movement = Path.G3

        # Add the path. This blocks until the path planner has capacity
        self.printer.path_planner.add_path(path)


    def get_description(self):
        return ("Counter-clockwise arc (experimental, not tested) "
               "")

