from __future__ import absolute_import

import re
from .MockPrinter import MockPrinter
from redeem.Gcode import Gcode
from redeem import __long_version__


class M115_Tests(MockPrinter):
  def test_gcodes_M115(self):

    g = Gcode({"message": "M115"})
    self.printer.processor.gcodes[g.gcode].execute(g)

    self.assertRegexpMatches(g.answer, "PROTOCOL_VERSION:\S+")
    self.assertRegexpMatches(g.answer, "REPLICAPE_KEY:TESTING_DUMMY_KEY")
    self.assertRegexpMatches(g.answer, "FIRMWARE_NAME:Redeem")
    self.assertRegexpMatches(g.answer, "FIRMWARE_VERSION:{}\s".format(re.escape(__long_version__)))
    self.assertRegexpMatches(g.answer, "FIRMWARE_URL:https:\S+")
    self.assertRegexpMatches(
        g.answer, "MACHINE_TYPE:{}\s".format(
            re.escape(self.printer.config.get('System', 'machine_type'))))
    self.assertRegexpMatches(g.answer, "EXTRUDER_COUNT:{}".format(self.printer.NUM_AXES - 3))
