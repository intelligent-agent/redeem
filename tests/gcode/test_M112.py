from __future__ import absolute_import

from .MockPrinter import MockPrinter
import mock
from Gcode import Gcode
from random import random
import math
import logging

class M112_Tests(MockPrinter):

    def test_gcodes_M112(self):
        self.printer.path_planner.emergency_interrupt = mock.Mock(return_value=None)
        self.execute_gcode("M112")
        self.printer.path_planner.emergency_interrupt.assert_called()
  
