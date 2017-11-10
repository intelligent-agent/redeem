from __future__ import absolute_import

from .MockPrinter import MockPrinter
import mock
from random import random
from Extruder import Heater

class M151_Tests(MockPrinter):

    @mock.patch.object(Heater, "enable_min_temp")
    def test_gcodes_M151(self, m):
        g = self.execute_gcode("M151")
        m.assert_called()

