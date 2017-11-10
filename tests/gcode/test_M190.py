from __future__ import absolute_import

import mock
from .MockPrinter import MockPrinter


class M190_Tests(MockPrinter):

    def setUp(self):
        self.printer.heaters['HBP'].set_target_temperature = mock.Mock()
        self.printer.processor.execute = mock.Mock()

    @mock.patch("gcodes.M190.Gcode")
    def test_gcodes_M190no_args(self, m):
        g = self.execute_gcode("M190")
        self.printer.heaters['HBP'].set_target_temperature.assert_called_with(0.0)
        m.assert_called_with({"message": "M116 P-1", "parent": g})
        self.printer.processor.execute.assert_called()

    @mock.patch("gcodes.M190.Gcode")
    def test_gcodes_M190_S123(self, m):
        g = self.execute_gcode("M190 S123")
        self.printer.heaters['HBP'].set_target_temperature.assert_called_with(123.0)
        m.assert_called_with({"message": "M116 P-1", "parent": g})
        self.printer.processor.execute.assert_called()
