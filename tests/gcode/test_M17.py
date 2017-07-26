from MockPrinter import MockPrinter
import mock
from random import random

class M17_Tests(MockPrinter):

    def setUp(self):
        for name, stepper in self.printer.steppers.iteritems():
            if self.printer.config.getboolean('Steppers', 'in_use_' + name):
                stepper.set_enabled = mock.Mock()

    def test_gcodes_M17(self):
        self.execute_gcode("M17")
        for name, stepper in self.printer.steppers.iteritems():
            if self.printer.config.getboolean('Steppers', 'in_use_' + name):
                stepper.set_enabled.assert_called()

