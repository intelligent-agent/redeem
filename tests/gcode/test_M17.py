from MockPrinter import MockPrinter
import mock
from six import iteritems


class M17_Tests(MockPrinter):

    def setUp(self):
        for name, stepper in iteritems(self.printer.steppers):
            if self.printer.config.getboolean('Steppers', 'in_use_' + name):
                stepper.set_enabled = mock.Mock()
        self.printer.path_planner.wait_until_done = mock.Mock()

    def test_gcodes_M17(self):
        self.execute_gcode("M17")
        self.printer.path_planner.wait_until_done.assert_called()
        for name, stepper in iteritems(self.printer.steppers):
            if self.printer.config.getboolean('Steppers', 'in_use_' + name):
                stepper.set_enabled.assert_called()

