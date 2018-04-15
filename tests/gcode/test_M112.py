from __future__ import absolute_import

import mock
from .MockPrinter import MockPrinter


class M112_Tests(MockPrinter):
  def test_gcodes_M112(self):
    self.printer.path_planner.emergency_interrupt = mock.Mock(return_value=None)
    self.execute_gcode("M112")
    self.printer.path_planner.emergency_interrupt.assert_called()
