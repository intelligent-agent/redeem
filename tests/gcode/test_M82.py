from __future__ import absolute_import

from .MockPrinter import MockPrinter
import mock
from random import random
from Path import Path

class M82_Tests(MockPrinter):

    def test_gcodes_M82_from_absolute(self):
        """ set state as it should be after a G90, all axes absolute """
        self.printer.axes_absolute = ["X", "Y", "Z", "E", "H", "A", "B", "C"]
        self.printer.axes_relative = []
        self.printer.movement == Path.ABSOLUTE
        self.execute_gcode("M82")
        self.assertEqual(self.printer.movement, Path.ABSOLUTE)
        self.assertEqual(self.printer.axes_absolute, ["X", "Y", "Z", "E", "H", "A", "B", "C"])
        self.assertEqual(self.printer.axes_relative, [])

    def test_gcodes_M82_from_relative(self):
        """ set state as it should be after a G91, all axes relative """
        self.printer.axes_absolute = []
        self.printer.axes_relative = ["X", "Y", "Z", "E", "H", "A", "B", "C"]
        self.printer.movement == Path.RELATIVE
        self.execute_gcode("M82")
        self.assertEqual(self.printer.movement, Path.MIXED)
        self.assertEqual(self.printer.axes_absolute, ["E", "H", "A", "B", "C"])
        self.assertEqual(self.printer.axes_relative, ["X", "Y", "Z"])

    def test_gcodes_M82_from_mixed(self):
        """ set state as it should be after a G90/M83, XYZ absolute and extruders relative """
        self.printer.axes_absolute = ["X", "Y", "Z"]
        self.printer.axes_relative = ["E", "H", "A", "B", "C"]
        self.printer.movement == Path.MIXED
        self.execute_gcode("M82")
        self.assertEqual(self.printer.movement, Path.ABSOLUTE)
        self.assertEqual(self.printer.axes_absolute, ["X", "Y", "Z", "E", "H", "A", "B", "C"])
        self.assertEqual(self.printer.axes_relative, [])

