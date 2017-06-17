import sys
sys.path.insert(0, '.') # tests/ = testing root folder

from MockPrinter import MockPrinter, Gcode, AbsolutePath, RelativePath, MixedPath
from testfixtures import Comparison as C

class GcodesTests(MockPrinter):

    """
    The following tests check that the path object that is sent to self.printer.path_planner
    matches what is expected, for [several variants of] each Gcode command
    """

    def test_gcodes_g1_g0_absolute(self):

        self.execute_gcode("G90")
        self.execute_gcode("M82")

        """ specifying feed rate and acceleration """
        self.execute_gcode("G1 X10 Y10 E3.1 F3000 Q3000")
        resulting_path = self.mock_path_planner.add_path.call_args[0][0]
        expected_path = AbsolutePath({"X":0.010*self.f, "Y":0.010*self.f, "E":0.0031*self.f}, 3000.0/60000*self.f, 3000.0*self.f/3600000)
        self.assertEqual(resulting_path, C(expected_path))

        """ test that we maintain current printer feed rate and accel, when not specified """
        self.printer.feed_rate=0.100
        self.printer.accel=0.025 / 60
        self.execute_gcode("G1 X20 Y20")
        resulting_path = self.mock_path_planner.add_path.call_args[0][0]
        expected_path = AbsolutePath({"X":0.020*self.f, "Y":0.020*self.f}, self.printer.feed_rate, self.printer.accel)
        self.assertEqual(resulting_path, C(expected_path))

    def test_gcodes_g1_g0_relative(self):
        self.execute_gcode("G91")
        self.execute_gcode("M83")
        self.execute_gcode("G1 X10 Y10 E10")

        gcode = Gcode({"message": "G1 X10 Y10 E10"})
        self.GP.execute(gcode)
        resulting_path = self.mock_path_planner.add_path.call_args[0][0]
        expected_path = RelativePath({"X":0.010*self.f, "Y":0.010*self.f, "E":0.010*self.f}, self.printer.feed_rate, self.printer.accel)
        self.assertEqual(resulting_path, C(expected_path))

    def test_gcodes_g1_g0_mixed(self):
        self.execute_gcode("G90")
        self.execute_gcode("M83")
        self.execute_gcode("G1 X10 Y10 E10")

        gcode = Gcode({"message": "G1 X10 Y10 E10"})
        self.GP.execute(gcode)
        resulting_path = self.mock_path_planner.add_path.call_args[0][0]
        expected_path = MixedPath({"X":0.010*self.f, "Y":0.010*self.f, "E":0.010*self.f}, self.printer.feed_rate, self.printer.accel)
        self.assertEqual(resulting_path, C(expected_path))

