from unittest import TestCase
import mock
from testfixtures import Comparison as C

import sys
sys.path.insert(0, '../redeem')

from Printer import Printer
from Path import Path, AbsolutePath, RelativePath, G92Path
from PathPlanner import PathPlanner
from GCodeProcessor import GCodeProcessor
from Gcode import Gcode

class GcodesTests(TestCase):

    def setUp(self):
        self.printer = Printer()
        self.printer.movement == Path.ABSOLUTE
        self.printer.feed_rate = 0.050 # m/s
        self.printer.accel = 0.050 / 60 # m/s/s
        
        Gcode.printer = self.printer
        Path.printer = self.printer

        self.mock_path_planner = mock.create_autospec(PathPlanner)
        self.printer.path_planner = self.mock_path_planner

        self.GP = GCodeProcessor(self.printer)

    def tearDown(self):
        pass


    """
    The following tests check that the path object that is sent to self.printer.path_planner
    matches what is expected, for [several variants of] each Gcode command
    """

    def test_gcodes_g1_g0_absolute(self):

        gcode = Gcode({"message": "G90"})
        self.GP.execute(gcode)
        gcode = Gcode({"message": "M82"})
        self.GP.execute(gcode)

        """ specifying feed rate and acceleration """
        gcode = Gcode({"message": "G1 X10 Y10 E3.1 F3000 Q3000"})
        self.GP.execute(gcode)
        resulting_path = self.mock_path_planner.add_path.call_args[0][0]
        expected_path = AbsolutePath({"X":0.010, "Y":0.010, "E":0.0031}, self.printer.feed_rate, self.printer.accel)
        self.assertEqual(resulting_path, C(expected_path))

        """ test that we maintain current printer feed rate and accel, when not specified """
        self.printer.feed_rate=0.100
        self.printer.accel=0.025 / 60
        gcode = Gcode({"message": "G1 X20 Y20"})
        self.GP.execute(gcode)
        resulting_path = self.mock_path_planner.add_path.call_args[0][0]
        expected_path = AbsolutePath({"X":0.020, "Y":0.020}, self.printer.feed_rate, self.printer.accel)
        self.assertEqual(resulting_path, C(expected_path))


    def test_gcodes_g1_g0_relative(self):
        gcode = Gcode({"message": "G91"})
        self.GP.execute(gcode)
        gcode = Gcode({"message": "M83"})
        self.GP.execute(gcode)

        gcode = Gcode({"message": "G1 X10 Y10 E5"})
        self.GP.execute(gcode)
        resulting_path = self.mock_path_planner.add_path.call_args[0][0]
        expected_path = RelativePath({"X":0.010, "Y":0.010, "E":0.005}, self.printer.feed_rate, self.printer.accel)
        self.assertEqual(resulting_path, C(expected_path))

