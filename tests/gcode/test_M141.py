from __future__ import absolute_import

from .MockPrinter import MockPrinter
import mock
from random import random
import logging

class M141_Tests(MockPrinter):

    @mock.patch.object(logging, "warning")
    def test_gcodes_M141_no_args(self, m):
        g = self.execute_gcode("M141")
        m.assert_called()

    @mock.patch.object(logging, "warning")
    def test_gcodes_M141_no_P(self, m):
        g = self.execute_gcode("M141 I1000 S0.5")
        m.assert_called()

    @mock.patch.object(logging, "warning")
    def test_gcodes_M141_no_I(self, m):
        g = self.execute_gcode("M141 P1 S0.5")
        m.assert_called()

    @mock.patch.object(logging, "warning")
    def test_gcodes_M141_no_S(self, m):
        g = self.execute_gcode("M141 P2 I1000")
        m.assert_called()

    @mock.patch.object(logging, "warning")
    def test_gcodes_M141_Pn_In_Sn(self, m):
        for i, v in enumerate(self.printer.fans):
            fan = i 
            freq = round(random()*10000,0)
            duty = round(random(),1)
            g = self.execute_gcode("M141 P"+str(fan)+" I"+str(freq)+" S"+str(duty))
            self.assertEqual(freq, self.printer.fans[i].pwm_frequency)
            self.assertEqual(duty, self.printer.fans[i].value)





