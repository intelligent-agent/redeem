from __future__ import absolute_import

import mock
from .MockPrinter import MockPrinter


class M117_Tests(MockPrinter):
  @mock.patch("redeem.gcodes.M117.Alarm.action_command")
  def test_gcodes_M117_no_space(self, m):
    self.execute_gcode("M117No leading space")
    m.assert_called_with('display_message', 'No leading space')

  @mock.patch("redeem.gcodes.M117.Alarm.action_command")
  def test_gcodes_M117_one_leading_space(self, m):
    self.execute_gcode("M117 One leading space")
    m.assert_called_with('display_message', 'One leading space')

  @mock.patch("redeem.gcodes.M117.Alarm.action_command")
  def test_gcodes_M117_multiple_leading_trailing_spaces(self, m):
    self.execute_gcode("M117    Leading/Trailing spaces  ")
    m.assert_called_with('display_message', '   Leading/Trailing spaces')

  @mock.patch("redeem.gcodes.M117.Alarm.action_command")
  def test_gcodes_M117_leading_digits(self, m):
    self.execute_gcode("M117 123 leading digits")
    m.assert_called_with('display_message', '123 leading digits')

  @mock.patch("redeem.gcodes.M117.Alarm.action_command")
  def test_gcodes_M117_leading_space_and_digit(self, m):
    self.execute_gcode("M117  123 leading space and digits")
    m.assert_called_with('display_message', ' 123 leading space and digits')
