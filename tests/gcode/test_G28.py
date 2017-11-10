from __future__ import absolute_import

from .MockPrinter import MockPrinter
from Gcode import Gcode

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

    def test_G28_is_buffered(self):
        g = Gcode({"message": "G28"})
        self.assertTrue(self.printer.processor.is_buffered(g))
