from __future__ import absolute_import

from .MockPrinter import MockPrinter
import mock
from Gcode import Gcode
from random import random
import math

class M110_Tests(MockPrinter):

    def setUp(self):
        Gcode.line_number = 99
        
    def test_gcodes_M110_no_param(self):
        self.execute_gcode("M110")
        self.assertEqual(Gcode.line_number, 0)
        
    def test_gcodes_M110_N123(self):
        self.execute_gcode("M110 N123")
        self.assertEqual(Gcode.line_number, 123)
        
