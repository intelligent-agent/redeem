from MockPrinter import MockPrinter
from Gcode import Gcode
import unittest

class G2_G3_Tests(MockPrinter):

    def test_G2_is_buffered(self):
        g = Gcode({"message": "G2"})
        self.assertTrue(self.printer.processor.is_buffered(g))

    def test_G3_is_buffered(self):
        g = Gcode({"message": "G3"})
        self.assertTrue(self.printer.processor.is_buffered(g))

    def test_G2_G3_TODO_Integrate_Andrew_Mirsky_code(self):
        raise unittest.SkipTest("Skipping G2/3 full testIntegrate. Code is in conflict state. See Andrew Mirsky's Pull Request")
