from __future__ import absolute_import

from .MockPrinter import MockPrinter
from Gcode import Gcode

class G20_G21_Tests(MockPrinter):

    def test_gcodes_G20(self):
        self.printer.unit_factor = 0.0
        self.execute_gcode("G20")
        self.assertEqual(self.printer.unit_factor, 25.4)

    def test_G20_is_not_buffered(self):
        g = Gcode({"message": "G20"})
        self.assertFalse(self.printer.processor.is_buffered(g))
    
    def test_gcodes_G21(self):
        self.printer.unit_factor = 0.0
        self.execute_gcode("G21")
        self.assertEqual(self.printer.unit_factor, 1.0)

    def test_G21_is_not_buffered(self):
        g = Gcode({"message": "G21"})
        self.assertFalse(self.printer.processor.is_buffered(g))

