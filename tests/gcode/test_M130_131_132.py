from __future__ import absolute_import

from .MockPrinter import MockPrinter
import mock
from random import random

class M130_M131_M132_Tests(MockPrinter):

    def setUp(self):
        for k in self.printer.heaters:
            self.printer.heaters[k].Kp = 1.0
            self.printer.heaters[k].Ti = 0.0
            self.printer.heaters[k].Td = 0.0
        self.heater_order = ["HBP", "E", "H", "A", "B", "C"]

    def test_gcodes_M130_no_args(self):
        g = self.execute_gcode("M130")
        self.assertEqual(self.printer.heaters["E"].Kp, 0.1) 

    def test_gcodes_M130_Pn_Sr(self):
        expected_Kp = {}
        for k in self.heater_order:
            expected_Kp[k] = round(random(), 2)
            self.execute_gcode("M130 P{} S{}".format(self.heater_order.index(k)-1, expected_Kp[k]))
            self.assertEqual(self.printer.heaters[k].Kp, expected_Kp[k]) 

    def test_gcodes_M131_Pn_Sr(self):
        expected_Ti = {}
        for k in self.heater_order:
            expected_Ti[k] = round(random(), 2)
            self.execute_gcode("M131 P{} S{}".format(self.heater_order.index(k)-1, expected_Ti[k]))
            self.assertEqual(self.printer.heaters[k].Ti, expected_Ti[k]) 

    def test_gcodes_M132_Pn_Sr(self):
        expected_Td = {}
        for k in self.heater_order:
            expected_Td[k] = round(random(), 2)
            self.execute_gcode("M132 P{} S{}".format(self.heater_order.index(k)-1, expected_Td[k]))
            self.assertEqual(self.printer.heaters[k].Td, expected_Td[k]) 


