from __future__ import absolute_import

from .MockPrinter import MockPrinter
import mock
from random import random

class M557_Tests(MockPrinter):

    def setUp(self):
        self.printer.probe_points = []

    def test_gcodes_M557_no_args(self):
        g = self.execute_gcode("M557")
        self.assertEqual(self.printer.probe_points, [])

    def test_gcodes_M557_valid_args(self):
        g = self.execute_gcode("M557 P0 X10 Y20.20 Z1.1")
        self.assertEqual(len(self.printer.probe_points), 1)
        self.assertEqual(self.printer.probe_points[0], {"X":10.0, "Y":20.2, "Z":1.1})

    def test_gcodes_M557_valid_args_G20_ignored(self):
        g = self.execute_gcode("G20")
        g = self.execute_gcode("M557 P0 X10 Y20.20 Z1.1")
        self.assertEqual(len(self.printer.probe_points), 1)
        self.assertEqual(self.printer.probe_points[0], {"X":10.0, "Y":20.2, "Z":1.1})

    def test_gcodes_M557_valid_args_no_Z(self):
        g = self.execute_gcode("M557 P0 X10 Y20.20")
        self.assertEqual(len(self.printer.probe_points), 1)
        self.assertEqual(self.printer.probe_points[0], {"X":10.0, "Y":20.2, "Z":0.0})

    def test_gcodes_M557_valid_args_2points(self):
        g = self.execute_gcode("M557 P0 X10 Y20.20 Z1.1")
        g = self.execute_gcode("M557 P1 X100 Y200 Z2.2")
        self.assertEqual(len(self.printer.probe_points), 2)
        self.assertEqual(self.printer.probe_points[0], {"X":10.0, "Y":20.2, "Z":1.1})
        self.assertEqual(self.printer.probe_points[1], {"X":100.0, "Y":200.0, "Z":2.2})

    """ 
    Current behaviour for Pn, where n > len(points) (by any amount) is to
    simply append to the points list. Thus, in the specific test below,  test,
    the P2 actually becomes P1 and is not considered an error. Whilst
    potentially confusing, I'm going to leave it as is and move on. Feel free
    to do something better.  Gruvin [deleting this comment is encouraged]
    """
    def test_gcodes_M557_P_out_of_bounds(self):
        g = self.execute_gcode("M557 P0 X10 Y20.20 Z1.1")
        g = self.execute_gcode("M557 P2 X100 Y200 Z2.2")
        self.assertEqual(len(self.printer.probe_points), 2)
        self.assertEqual(self.printer.probe_points[0], {"X":10.0, "Y":20.2, "Z":1.1})
        self.assertEqual(self.printer.probe_points[1], {"X":100.0, "Y":200.0, "Z":2.2})
