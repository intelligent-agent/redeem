"""
GCode M109
Set extruder temperature and wait for it to be reached

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




class M109(GCodeCommand):

    def execute(self, g):
        m104 = Gcode({"message": "M104 " + " ".join(g.get_tokens()),
                      "prot": g.prot})
        self.printer.processor.execute(m104)
        m116 = Gcode({"message": "M116", "prot": g.prot})
        self.printer.processor.execute(m116)

    def get_description(self):
        return "Set extruder temperature and wait for it to be reached"
