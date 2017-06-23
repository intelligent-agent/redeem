from MockPrinter import MockPrinter
from mock import MagicMock
from Path import Path

class G1_G0_Tests(MockPrinter):


    """
    The following tests check that the path object that is sent to self.printer.path_planner
    matches what is expected, for [several variants of] each Gcode command
    """

    def test_gcodes_G1_G0_absolute(self):
        self.printer.movement = Path.ABSOLUTE

        """ specifying feed rate and acceleration """
        self.execute_gcode("G1 X10 Y10 E3.1 F3000 Q3000")
        expected_path = self.AbsolutePath({"X":0.010*self.f, "Y":0.010*self.f, "E":0.0031*self.f}, 3000.0/60000*self.f, 3000.0*self.f/3600000)
        self.printer.path_planner.add_path.called_with(expected_path)

        """ test that we maintain current printer feed rate and accel, when not specified """
        self.printer.feed_rate=0.100
        self.printer.accel=0.025 / 60
        self.execute_gcode("G1 X20 Y20")
        expected_path = self.AbsolutePath({"X":0.020*self.f, "Y":0.020*self.f}, self.printer.feed_rate, self.printer.accel)
        self.printer.path_planner.add_path.called_with(expected_path)

    def test_gcodes_G1_G0_relative(self):
        self.printer.movement = Path.RELATIVE

        expected_path = self.RelativePath({"X":0.010*self.f, "Y":0.010*self.f, "E":0.010*self.f}, self.printer.feed_rate, self.printer.accel)
        self.printer.path_planner.add_path.called_with(expected_path)

    def test_gcodes_G1_G0_mixed(self):
        self.printer.movement = Path.MIXED
        
        self.execute_gcode("G1 X10 Y10 E10")
        expected_path = self.MixedPath({"X":0.010*self.f, "Y":0.010*self.f, "E":0.010*self.f}, self.printer.feed_rate, self.printer.accel)
        self.printer.path_planner.add_path.called_with(expected_path)

