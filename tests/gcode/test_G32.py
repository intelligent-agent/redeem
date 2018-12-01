from __future__ import absolute_import

import mock
from .MockPrinter import MockPrinter
from redeem.Gcode import Gcode


class G32_Tests(MockPrinter):
  def test_G32_properties(self):
    self.assertGcodeProperties("G32", is_buffered=True)

  @mock.patch("redeem.gcodes.G32.Gcode")
  def test_G32_runs_macro(self, mock_Gcode):
    self.printer.processor.execute = mock.Mock()    # prevent macro command execution
    macro_gcodes = self.printer.config.get("Macros", "G32").split("\n")

    self.execute_gcode("G32")
    """ compare macro from config, to macro commands executed """
    for i, v in enumerate(macro_gcodes):
      self.assertEqual(v, mock_Gcode.call_args_list[i][0][0]["message"])
