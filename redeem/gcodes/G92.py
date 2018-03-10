"""
GCode G92
Set current position of steppers without moving them

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

import logging
from .GCodeCommand import GCodeCommand
from redeem.Path import G92Path


class G92(GCodeCommand):

    def execute(self, g):
        AXES = self.printer.AXES[:self.printer.NUM_AXES]
        if g.num_tokens() == 0:
            # If no token is present, do this for all steppers
            logging.debug("Adding all to G92")
            g.set_tokens([v + "0" for v in AXES]) # ["X0", "Y0", ...]
        pos = {}
        for axis in AXES:
            if g.has_letter(axis):
                real_axis = self.printer.movement_axis(axis)
                pos[real_axis] = g.get_distance_by_letter(axis) / 1000.0 # SI m

        # Make a path segment from the axes
        path = G92Path(pos, self.printer.feed_rate)
        self.printer.path_planner.add_path(path)

    def get_description(self):
        return "Set the current position of steppers without moving them"

    def is_buffered(self):
        return True

    def is_async(self):
        return True

    def get_test_gcodes(self):
        return ["G92"]

