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
        if g.has_letter("S"):  # Get the feed rate
            level = g.get_int_by_letter("S", 20)
            if level in [10, 20, 30, 40, 50, 60]:
                logging.getLogger().setLevel(level)
                logging.info("Debug level set to "+str(level))


    def get_description(self):
        return "Set debug level"

    def is_buffered(self):
        return True
