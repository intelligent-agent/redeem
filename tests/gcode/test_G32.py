from MockPrinter import MockPrinter
from Gcode import Gcode
import unittest

class G32_Tests(MockPrinter):

    def test_G32_is_buffered(self):
        g = Gcode({"message": "G31"})
        self.assertTrue(self.printer.processor.is_buffered(g))

    def test_G32_skipping_becasue_macro(self):
        raise unittest.SkipTest("Skipping full G32 test because it runs a macro containing many, random Gcodes")
