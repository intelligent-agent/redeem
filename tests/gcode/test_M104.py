from __future__ import absolute_import

from .MockPrinter import MockPrinter
import mock
from Path import Path
from random import random

class M104_Tests(MockPrinter):

    def test_gcodes_M104_no_args(self):
        self.printer.current_tool = "E" 
        self.printer.heaters[self.printer.current_tool] = mock.Mock()
        self.execute_gcode("M104")
        self.printer.heaters[self.printer.current_tool].set_target_temperature.assert_called_with(0.0)

    @mock.patch("logging.warning")
    def test_gcodes_M104_bad_P(self, m):
        g = self.execute_gcode("M104 P999 S0")
        m.assert_called()

    def test_gcodes_M104_Pn_Sx(self):
        for i, n in enumerate("EH"):
            self.printer.heaters[n].set_target_temperature = mock.Mock()
            test_temp = round(random()*100,2)
            test_code = "M104 P"+str(i)+" S"+str(test_temp)
            self.execute_gcode(test_code)
            self.printer.heaters[n].set_target_temperature.assert_called_with(test_temp)





