"""
GCode M206 - set home offset

Author: Boris Lasic
email: boris(at)max(dot)si
Website: http://www.max.si
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
try:
    from redeem.Path import Path
except ImportError:
    from Path import Path
import logging

class M206(GCodeCommand):

    def execute(self, g):
        tokens = g.get_tokens()
        if len(tokens) > 0:
            axis = tokens[0]
            if not axis in self.printer.path_planner.center_offset:
                logging.warning("M206: Wrong axis {}".format(axis))
                return
            try:
                offset = float(tokens[1])
            except ValueError:
                logging.warning("Not a float: {}".format(tokens[1]))
                return
            self.printer.path_planner.center_offset[axis] = offset
            logging.info("Updated offset for {} to {}".format(axis, offset))
        else:
            g.set_answer("ok "+", ".join(["{}: {}".format(k, v) for k,v in sorted(self.printer.path_planner.center_offset.iteritems())]))

    def get_description(self):
        return "Set or get end stop offsets"
    
    def get_long_description(self):
        return ("If no parameters are given, get the current X, Y and Z end stop offsets. " 
                "To set offset, first token is axis, second is offset. Negative values are OK"
                "Example: M206 X 0.01")
