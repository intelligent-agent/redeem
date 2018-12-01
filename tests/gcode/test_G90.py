from __future__ import absolute_import

from .MockPrinter import MockPrinter
from redeem.Path import Path
from redeem.Gcode import Gcode


class G90_Tests(MockPrinter):
  def test_G90_properties(self):
    self.assertGcodeProperties("G90", is_buffered=True, is_async=True)

  def test_gcodes_G90_from_absolute(self):
    self.printer.axes_absolute = ["X", "Y", "Z", "E", "H", "A", "B", "C"]
    self.printer.axes_relative = []
    self.printer.movement = Path.ABSOLUTE
    self.execute_gcode("G90")
    self.assertEqual(self.printer.movement, Path.ABSOLUTE)
    self.assertEqual(self.printer.axes_absolute, ["X", "Y", "Z", "E", "H", "A", "B", "C"])
    self.assertEqual(self.printer.axes_relative, [])

  def test_gcodes_G90_from_relative(self):
    self.printer.axes_relative = ["X", "Y", "Z", "E", "H", "A", "B", "C"]
    self.printer.axes_absolute = []
    self.printer.movement = Path.RELATIVE
    self.execute_gcode("G90")
    self.assertEqual(self.printer.movement, Path.ABSOLUTE)
    self.assertEqual(self.printer.axes_absolute, ["X", "Y", "Z", "E", "H", "A", "B", "C"])
    self.assertEqual(self.printer.axes_relative, [])

  def test_gcodes_G90_from_mixed(self):
    self.printer.axes_absolute = ["X", "Y", "Z"]
    self.printer.axes_relative = ["E", "H", "A", "B", "C"]
    self.printer.movement = Path.RELATIVE
    self.execute_gcode("G90")
    self.assertEqual(self.printer.movement, Path.ABSOLUTE)
    self.assertEqual(self.printer.axes_absolute, ["X", "Y", "Z", "E", "H", "A", "B", "C"])
    self.assertEqual(self.printer.axes_relative, [])
