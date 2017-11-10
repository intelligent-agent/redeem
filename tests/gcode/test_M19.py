from __future__ import absolute_import

from .MockPrinter import MockPrinter
import mock
from redeem.Stepper import Stepper_00A4


class M19_Tests(MockPrinter):

    @mock.patch.object(Stepper_00A4, "reset")
    def test_gcodes_M19(self, m):
        self.execute_gcode("M19")
        self.printer.path_planner.wait_until_done.assert_called()
        for name, stepper in self.printer.steppers.iteritems():
            if self.printer.config.getboolean('Steppers', 'in_use_' + name):
                m.assert_called()

