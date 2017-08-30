"""
GCode M290
Babystepping

Author: Elias Bakken
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import logging


class M290(GCodeCommand):

    def execute(self, g):
        if g.has_letter("S"): # Amount in mm
            offset_z = g.get_float_by_letter("S")
            self.printer.offset_z += (offset_z/1000.0)
        else:
            g.set_answer("ok Current Babystep offset: {} mm".format(self.printer.offset_z*1000.0))

    def get_description(self):
        return "Baby stepping"

    def get_long_description(self):
        return ("Baby stepping. This command tells the printer to apply the specified "
                "additional offset to the Z coordinate for all future moves, "
                "and to apply the offset to moves that have already been "
                "queued if this case be done. Baby stepping is cumulative, "
                "for example after M290 S0.1 followed by M290 S-0.02, "
                "an offset of 0.08mm is used.\n"
                "M290 with no parameters reports the accumulated baby stepping offset.\n"
                "The baby stepping offset is reset to zero when the printer is "
                "homed or the bed is probed.")
