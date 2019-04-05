from __future__ import absolute_import

import mock
import math
from random import random
from .MockPrinter import MockPrinter
from redeem.Fan import Fan


class M106_M107_Tests(MockPrinter):
  def setUp(self):
    self.fan1 = mock.Mock()
    self.fan2 = mock.Mock()
    self.printer.fans = [self.fan1, self.fan2]
    self.printer.controlled_fans = [self.fan2]

  def test_gcodes_M106_no_params(self):
    self.execute_gcode("M106")
    self.fan2.set_value.assert_called_with(1.0)

  def test_gcodes_M106_P0_S128(self):
    self.execute_gcode("M106 P0 S128")
    self.fan1.set_value.assert_called_with(128.0 / 255.0)

  def test_gcodes_M106_P1_S128(self):
    test_value = math.floor(random() * 255.0)
    self.execute_gcode("M106 P1 S{:.2f}".format(test_value))
    self.fan2.set_value.assert_called_with(test_value / 255.0)

  @mock.patch.object(Fan, "ramp_to", return_value=None)
  def test_gcodes_M106_P1_S128_R(self, mock_ramp_to):
    self.execute_gcode("M106 P0 S128 R")
    self.fan1.ramp_to.assert_called_with(128.0 / 255.0, 0.01)

  @mock.patch.object(Fan, "ramp_to", return_value=None)
  def test_gcodes_M106_P1_S128_R0p2(self, mock_ramp_to):
    self.execute_gcode("M106 P0 S128 R0.2")
    self.fan1.ramp_to.assert_called_with(128.0 / 255.0, 0.2)

  def test_gcodes_M107_no_params(self):
    self.fan2.set_value(1.0)
    self.execute_gcode("M107")
    self.fan2.set_value.assert_called_with(0.0)

  def test_gcodes_M107_P1(self):
    self.fan1.set_value(1.0)
    self.execute_gcode("M107 P0")
    self.fan1.set_value.assert_called_with(0.0)
