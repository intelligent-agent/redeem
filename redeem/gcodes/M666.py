"""
GCode M666
Set or get endstop offset value

Author: Elias Bakken
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from GCodeCommand import GCodeCommand
import logging
from six import iteritems


class M666(GCodeCommand):
    def execute(self, g):
        offset = self.printer.path_planner.center_offset
           
        if g.num_tokens() == 0:
            g.set_answer("ok " + ' '.join('%s:%.1f mm' % (i[0], i[1]*1000) for i in sorted(
                iteritems(offset))))
        else:
            for axis in self.printer.path_planner.center_offset.keys():
                if g.has_letter(axis):
                    offset[axis] = g.get_float_by_letter(axis) / 1000.
                    logging.info("M666: Set axis %s offset to %f",
                                 axis, offset[axis])

    def get_description(self):
        return "Set or get axis offset values"

    def get_long_description(self):
        return ("Set or get axis offset values. "
                "If no tokens are given, reuturn the current offset values."
                "If tokens are given, set the offset value to each of the tokens given in mm.\n"
                "Format: M666 <axis1><offset1> <axis2>offset2> \n"
                "Example: 'M666 X200' sets the X-axis to have offset 200 mm.\n"
                "This M-code is to set the offset, to adjust the offset, use M206")

