from __future__ import absolute_import

from .MockPrinter import MockPrinter
from mock import MagicMock
from Path import *

class G1_G0_Tests(MockPrinter):


    """
    The following tests check that the path object that is sent to self.printer.path_planner
    matches what is expected, for [several variants of] each Gcode command
    """

    def test_gcodes_G1_G0_absolute(self):
        self.printer.movement = Path.ABSOLUTE

        """ specifying feed rate and acceleration """
        self.execute_gcode("G1 X10 Y10 E3.1 F3000 Q3000")
        expected_path = AbsolutePath({"X":0.010*self.f, "Y":0.010*self.f, "E":0.0031*self.f}, 3000.0/60000*self.f, 3000.0*self.f/3600000)
        self.printer.path_planner.add_path.called_with(expected_path)

        """ test that we maintain current printer feed rate and accel, when not specified """
        self.printer.feed_rate=0.100
        self.printer.accel=0.025 / 60
        self.execute_gcode("G1 X20 Y20")
        expected_path = AbsolutePath({"X":0.020*self.f, "Y":0.020*self.f}, self.printer.feed_rate, self.printer.accel)
        self.printer.path_planner.add_path.called_with(expected_path)

    def test_gcodes_G1_G0_relative(self):
        self.printer.movement = Path.RELATIVE

        expected_path = RelativePath({"X":0.010*self.f, "Y":0.010*self.f, "E":0.010*self.f}, self.printer.feed_rate, self.printer.accel)
        self.printer.path_planner.add_path.called_with(expected_path)

    def test_gcodes_G1_G0_mixed(self):
        self.printer.movement = Path.MIXED
        
        self.execute_gcode("G1 X10 Y10 E10")
        expected_path = MixedPath({"X":0.010*self.f, "Y":0.010*self.f, "E":0.010*self.f}, self.printer.feed_rate, self.printer.accel)
        self.printer.path_planner.add_path.called_with(expected_path)

    def test_gcodes_G1_G0_syntax(self):
        g = self.execute_gcode("G1X1Y2.3 z-0.456E+7.89ab c")
        self.assertEqual(g.tokens, ['X1', 'Y2.3', 'Z-0.456', 'E+7.89', 'A', 'B', 'C'])

    def test_gcodes_G1_G0_M117_exception(self):
        g = self.execute_gcode("M117     123G1X1Y2.3 z-0.456E+7.89ab c")
        self.assertEqual(g.gcode, 'M117')
        self.assertEqual(g.tokens[0], "G1")
        self.assertEqual(g.message, "M117     123G1X1Y2.3 z-0.456E+7.89ab c")
