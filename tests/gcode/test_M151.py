from __future__ import absolute_import

import mock
from .MockPrinter import MockPrinter
from redeem.Extruder import Heater


class M151_Tests(MockPrinter):

    @mock.patch.object(Heater, "enable_min_temp")
    def test_gcodes_M151(self, m):
        g = self.execute_gcode("M151")
        m.assert_called()

