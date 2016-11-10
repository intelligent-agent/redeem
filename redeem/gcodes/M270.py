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

import logging


class M270(GCodeCommand):

    def execute(self, g):
        if g.has_letter("S"):
            axis_config = int(g.get_value_by_letter("S"))
            if axis_config in [0, 1, 2, 3]:
                self.printer.axis_config = axis_config
                logging.info("Coordinate system set to " + str(self.printer.axis_config))
        else:
            g.set_answer("ok "+"Current axis config is: {}".format(self.printer.axis_config))


    def get_long_description(self):
        return ("Set coordinate system. Parameter S set the type, which is "
                "0 = Cartesian, 1 = H-belt, 2 = CoreXY, 3 = Delta")

    def get_description(self):
        return "Set coordinate system"
