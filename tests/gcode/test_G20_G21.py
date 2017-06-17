from MockPrinter import MockPrinter

class G20_G21_Tests(MockPrinter):

    def test_gcodes_G20(self):
        self.printer.factor = 0.0
        self.execute_gcode("G20")
        self.assertEqual(self.printer.factor, 25.4)

    def test_gcodes_G21(self):
        self.printer.factor = 0.0
        self.execute_gcode("G21")
        self.assertEqual(self.printer.factor, 1.0)


