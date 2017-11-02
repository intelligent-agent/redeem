from MockPrinter import MockPrinter
import mock
from six import iteritems
from Stepper import Stepper

class M18_Tests(MockPrinter):

    def setUp(self):
        for name, stepper in iteritems(self.printer.steppers):
            if self.printer.config.getboolean('Steppers', 'in_use_' + name):
                stepper.set_disabled = mock.Mock()
        self.printer.path_planner.wait_until_done = mock.Mock()
        Stepper.set_stepper_power_down = mock.Mock()

    def test_gcodes_M18_no_args(self):
        self.execute_gcode("M18")
        self.printer.path_planner.wait_until_done.assert_called()
        for name, stepper in iteritems(self.printer.steppers):
            if self.printer.config.getboolean('Steppers', 'in_use_' + name):
                stepper.set_disabled.assert_called()

    def test_gcodes_M18_X_Y(self):
        self.execute_gcode("M18 X Y")
        self.printer.path_planner.wait_until_done.assert_called()
        for name, stepper in iteritems(self.printer.steppers):
            if self.printer.config.getboolean('Steppers', 'in_use_' + name):
                if name in ["X", "Y"]:
                    stepper.set_disabled.assert_called()
                else:
                    stepper.set_disabled.assert_not_called()

    def test_gcodes_M18_D_no_arg(self):
        self.execute_gcode("M18 D")
        Stepper.set_stepper_power_down.assert_called_with(False)

    def test_gcodes_M18_D1(self):
        self.execute_gcode("M18 D0")
        Stepper.set_stepper_power_down.assert_called_with(False)

    def test_gcodes_M18_D1(self):
        self.execute_gcode("M18 D1")
        Stepper.set_stepper_power_down.assert_called_with(True)
