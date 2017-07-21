from MockPrinter import MockPrinter
import mock
from Gcode import Gcode
import re
import logging
import time


def mock_sleep(t):
    global heaters
    mock_sleep.counter += 1 
    for heater in heaters:
        if mock_sleep.counter == heaters.keys().index(heater): 
            print "Heater {} target reched".format(heater)
            heaters[heater].is_target_temperature_reached.return_value = True
    return None
mock_sleep.counter = 0

class M116_Tests(MockPrinter):

    def setUp(self):
        global heaters
        heaters = self.printer.heaters
        for v in self.printer.heaters:
            self.printer.heaters[v].is_target_temperature_reached.return_value = False

    @mock.patch("gcodes.M116.time.sleep", side_effect=mock_sleep) 
    def test_gcodes_M116_no_param(self, m):

        self.printer.processor.execute = mock.Mock() # mock M116's call to M105
        self.execute_gcode("M116")

        for v in self.printer.heaters:
            self.assertTrue(self.printer.heaters[v].is_target_temperature_reached())
