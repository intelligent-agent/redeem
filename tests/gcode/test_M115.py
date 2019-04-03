from __future__ import absolute_import

import mock
import re
from .MockPrinter import MockPrinter
from redeem.Gcode import Gcode
from redeem import __long_version__
from six import PY2


class M115_Tests(MockPrinter):
  @mock.patch('redeem.gcodes.M115.open', mock.mock_open(read_data='halloween bumpkins'))
  def test_gcodes_M115(self):

    g = Gcode({"message": "M115"})
    self.printer.processor.gcodes[g.gcode].execute(g)

    self.assertRegex(g.answer, "PROTOCOL_VERSION:\S+")
    self.assertRegex(g.answer, "REPLICAPE_KEY:TESTING_DUMMY_KEY")
    self.assertRegex(g.answer, "FIRMWARE_NAME:Redeem")
    self.assertRegex(g.answer, "FIRMWARE_VERSION:{}\s".format(re.escape(__long_version__)))
    self.assertRegex(g.answer, "FIRMWARE_URL:https:\S+")
    self.assertRegex(
        g.answer, "MACHINE_TYPE:{}\s".format(
            re.escape(self.printer.config.get('System', 'machine_type'))))
    self.assertRegex(g.answer, "EXTRUDER_COUNT:{}".format(self.printer.NUM_EXTRUDERS))
    self.assertRegex(g.answer, "DISTRIBUTION_NAME:halloween DISTRIBUTION_VERSION:bumpkins")

  if PY2:

    def assertRegex(self, string, expected):
      self.assertRegexpMatches(string, expected)
