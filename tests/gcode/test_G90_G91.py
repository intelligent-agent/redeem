from MockPrinter import MockPrinter
import mock
from Path import Path
from Gcode import Gcode

class G90_G91_Tests(MockPrinter):

    def test_G90_is_buffered(self):
        g = Gcode({"message": "G90"})
        self.assertTrue(self.printer.processor.is_buffered(g))

    def test_gcodes_G90(self):
        self.printer.movement = Path.RELATIVE
        self.execute_gcode("G90")
        self.assertEqual(self.printer.movement, Path.ABSOLUTE)

    def test_G91_is_buffered(self):
        g = Gcode({"message": "G91"})
        self.assertTrue(self.printer.processor.is_buffered(g))

    def test_gcodes_G91(self):
        self.printer.movement = Path.ABSOLUTE
        self.execute_gcode("G91")
        self.assertEqual(self.printer.movement, Path.RELATIVE)
