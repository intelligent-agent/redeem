"""
GCode M190
Set heated bed temperature and for it to be reached

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
try:
    from Gcode import Gcode
except ImportError:
    from redeem.Gcode import Gcode

class M190(GCodeCommand):

    def execute(self, g):
        temperature = float(g.get_value_by_letter("S"))
        self.printer.heaters['HBP'].set_target_temperature(temperature)
        self.printer.processor.execute(Gcode({"message": "M116",
                                              "prot": g.prot}))

    def get_description(self):
        return "Set heated bed temperature and wait for it to be reached"

    def is_buffered(self):
        return True
