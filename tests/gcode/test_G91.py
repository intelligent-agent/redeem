from __future__ import absolute_import

from .MockPrinter import MockPrinter
import mock
from Path import Path
from Gcode import Gcode

class G91_Tests(MockPrinter):

    def test_G91_is_buffered(self):
        g = Gcode({"message": "G90"})
        self.assertTrue(self.printer.processor.is_buffered(g))

    def test_gcodes_G91_from_absolute(self):
        self.printer.axes_absolute = ["X", "Y", "Z", "E", "H", "A", "B", "C"]
        self.printer.axes_relative = []
        self.printer.movement = Path.ABSOLUTE
        self.execute_gcode("G91")
        self.assertEqual(self.printer.movement, Path.RELATIVE)
        self.assertEqual(self.printer.axes_absolute, [])
        self.assertEqual(self.printer.axes_relative, ["X", "Y", "Z", "E", "H", "A", "B", "C"])

    def test_gcodes_G91_from_relative(self):
        self.printer.axes_relative = ["X", "Y", "Z", "E", "H", "A", "B", "C"]
        self.printer.axes_absolute = []
        self.printer.movement = Path.RELATIVE
        self.execute_gcode("G91")
        self.assertEqual(self.printer.movement, Path.RELATIVE)
        self.assertEqual(self.printer.axes_absolute, [])
        self.assertEqual(self.printer.axes_relative, ["X", "Y", "Z", "E", "H", "A", "B", "C"])

    def test_gcodes_G91_from_mixed(self):
        self.printer.axes_absolute = ["X", "Y", "Z"]
        self.printer.axes_relative = ["E", "H", "A", "B", "C"]
        self.printer.movement = Path.RELATIVE
        self.execute_gcode("G91")
        self.assertEqual(self.printer.movement, Path.RELATIVE)
        self.assertEqual(self.printer.axes_absolute, [])
        self.assertEqual(self.printer.axes_relative, ["X", "Y", "Z", "E", "H", "A", "B", "C"])
