from __future__ import absolute_import
from six import iteritems

from .MockPrinter import MockPrinter
import mock
from random import random

class M140_Tests(MockPrinter):

    def setUp(self):
        for _, v in iteritems(self.printer.heaters):
            v.target_temp = 12.34

    def test_gcodes_M140_no_args(self):
        g = self.execute_gcode("M140")
        self.assertEqual(self.printer.heaters['HBP'].target_temp, 0.0)

    def test_gcodes_M140_S60(self):
        g = self.execute_gcode("M140 S60")
        self.assertEqual(self.printer.heaters['HBP'].target_temp, 60.0)




