"""
GCode M109
Set extruder temperature and wait for it to be reached

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

from .GCodeCommand import GCodeCommand
from redeem.Gcode import Gcode


class M109(GCodeCommand):
  def execute(self, g):
    m104 = Gcode({"message": "M104 " + " ".join(g.get_tokens()), "parent": g})
    self.printer.processor.resolve(m104)
    self.printer.processor.execute(m104)

    has_parameter = g.has_letter("P") or g.has_letter("T")
    if not has_parameter:
      heaters = ["E", "H"]
      if self.printer.config.get('Configuration', 'reach') != "None":
        heaters.extend(["A", "B", "C"])
      parameters = ["P" + str(heaters.index(self.printer.current_tool))]
    else:
      parameters = g.get_tokens()

    m116 = Gcode({"message": "M116 " + " ".join(parameters), "parent": g})
    self.printer.processor.resolve(m116)
    self.printer.processor.execute(m116)

  def get_description(self):
    return "Set extruder temperature and wait for it to be reached"

  def is_buffered(self):
    return True
