from MockPrinter import MockPrinter
import mock
from Path import Path
from random import random

class M104_Tests(MockPrinter):

    def test_gcodes_M104_no_args(self):
        self.assertFalse(self.execute_gcode("M104"))

    def test_gcodes_M104_bad_P(self):
        self.assertFalse(self.execute_gcode("M104 P999 S0"))

    def test_gcodes_M104_Pn_Sx(self):
        for i, n in enumerate("EH"):
            self.printer.heaters[n].set_target_temperature = mock.Mock()
            test_temp = round(random()*100,2)
            test_code = "M104 P"+str(i)+" S"+str(test_temp)
            print "@#$@#%!#%$$%#!: ",test_code
            self.execute_gcode(test_code)
            self.printer.heaters[n].set_target_temperature.assert_called_with(test_temp)





