from __future__ import absolute_import

import mock
from .MockPrinter import MockPrinter
from redeem.Gcode import Gcode


class G4_Tests(MockPrinter):
  def test_G4_properties(self):
    self.assertGcodeProperties("G4", is_buffered=True)

  @mock.patch('time.sleep')
  def test_G4_milliseconds(self, mock_time):
    self.execute_gcode("G4 P1234")
    mock_time.assert_called_with(1.234)

  @mock.patch('time.sleep')
  def test_G4_seconds(self, mock_time):
    self.execute_gcode("G4 S1.234")
    mock_time.assert_called_with(1.234)
