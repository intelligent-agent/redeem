from __future__ import absolute_import

from .MockPrinter import MockPrinter
import mock
from Gcode import Gcode
from random import random
import math

class M108_Tests(MockPrinter):

    def test_gcodes_M108(self):
        self.printer.running_M116 = True
        self.execute_gcode("M108")
        self.assertEqual(self.printer.running_M116, False)

