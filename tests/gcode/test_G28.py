from __future__ import absolute_import

from .MockPrinter import MockPrinter
from redeem.Gcode import Gcode


class G28_Tests(MockPrinter):
  def test_gcodes_G28_home_all(self):
    self.execute_gcode("G28")
    self.printer.path_planner.home.assert_called_with(["X", "Y", "Z"])

  def test_gcodes_G28_home_XY(self):
    self.execute_gcode("G28 X0 Y0")
    self.printer.path_planner.home.assert_called_with(["X", "Y"])

  def test_gcodes_G28_home_Z(self):
    self.execute_gcode("G28 Z0")
    self.printer.path_planner.home.assert_called_with(["Z"])

  def test_G28_properties(self):
    self.assertGcodeProperties("G28", is_buffered=True, is_async=True)
