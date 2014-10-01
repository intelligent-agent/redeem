"""
GCode M270
Set coordinate system:
0 - Cartesian
1 - H-bot
2 - CoreXY
3 - Delta bot (Rostock type)

Author: Elias Bakken
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
try:
    from Path import Path
except ImportError:
    from redeem.Path import Path

import logging


class M270(GCodeCommand):

    def execute(self, g):
        if g.has_letter("S"):
            axis_config = int(g.get_value_by_letter("S"))
            if axis_config in [0, 1, 2, 3]:
                Path.axis_config = axis_config
                logging.info("Coordinate system set to " + str(axis_config))

    def get_description(self):
        return "Set coordinate system"
