from MockPrinter import MockPrinter
from Gcode import Gcode
import unittest

class G31_Tests(MockPrinter):

    def test_G31_is_buffered(self):
        g = Gcode({"message": "G31"})
        self.assertTrue(self.printer.processor.is_buffered(g))

    def test_G31_skipping_becasue_macro(self):
        raise unittest.SkipTest("Skipping full G31 test because it runs a macro containing many, random Gcodes")
