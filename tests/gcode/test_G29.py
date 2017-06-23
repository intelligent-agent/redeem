from MockPrinter import MockPrinter
from Gcode import Gcode
import unittest

class G29_Tests(MockPrinter):

    def test_G29_is_buffered(self):
        g = Gcode({"message": "G29"})
        self.assertTrue(self.printer.processor.is_buffered(g))

    def test_G29_skipping_becasue_macro(self):
        raise unittest.SkipTest("Skipping full G29 test because it runs a macro containing many, random Gcodes")
