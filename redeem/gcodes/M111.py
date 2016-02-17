"""
GCode M111
Set debug level

Author: Elias Bakken
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
try:
    from Gcode import Gcode
except ImportError:
    from redeem.Gcode import Gcode
import logging

class M111(GCodeCommand):

    def execute(self, g):
        level = g.get_int_by_letter("S", 20)
        if level in [10, 20, 30, 40, 50, 60]:
            logging.getLogger().setLevel(level)
            if hasattr(self.printer, "redeem_logging_handler"):
                self.printer.redeem_logging_handler.setLevel(level)
            logging.info("Debug level set to "+str(level))


    def get_description(self):
        return "Set debug level"

    def get_long_description(self):
        return ("set debug level, S sets the level. If no S is present, it is set to 20 = Info")

    def is_buffered(self):
        return True
