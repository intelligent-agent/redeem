from MockPrinter import MockPrinter
import mock
from Gcode import Gcode
import re
import logging
import time


global counter
global printer

"""
This function replaces gcodes.M116.time.sleep() for these tests.
A counter is incremented at each call. Each multiple of ten triggers
a mock is_target_temperature_reached() method to return True, for
mock heaters E, H, HBP, A, B and C, in that order.
"""
def mock_sleep(t):
    global counter
    global printer

    counter += 1 
    if counter == 10:
        print "E target reched"
        printer.heaters['E'].is_target_temperature_reached.return_value = True
    elif counter == 20:
        print "H target reched"
        printer.heaters['H'].is_target_temperature_reached.return_value = True
    elif counter == 30:
        print "HBP target reched"
        printer.heaters['HBP'].is_target_temperature_reached.return_value = True
    return None

class M116_Tests(MockPrinter):

    def setUp(self):
        global counter
        global printer 
        counter=0
        printer = self.printer
        printer.heaters['E'].is_target_temperature_reached.return_value = False
        printer.heaters['H'].is_target_temperature_reached.return_value = False
        printer.heaters['HBP'].is_target_temperature_reached.return_value = False

    @mock.patch("gcodes.M116.time.sleep", side_effect=mock_sleep) 
    def test_gcodes_M116_no_param(self, m):
        global counter
        self.printer.processor.execute = mock.Mock() # block M116's call to M105
        
        self.execute_gcode("M116")

        E = self.printer.heaters['E'].is_target_temperature_reached()
        H = self.printer.heaters['H'].is_target_temperature_reached()
        HBP = self.printer.heaters['HBP'].is_target_temperature_reached()
        self.assertTrue(E)
        self.assertTrue(H)
        self.assertTrue(HBP)
