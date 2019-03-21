from __future__ import absolute_import

import mock
from .MockPrinter import MockPrinter


class M109_Tests(MockPrinter):
  def setUp(self):
    self.mock_execute = self.printer.processor.execute = mock.Mock(autospec=True, return_value=None)

  def test_gcodes_M109_S123(self):
    self.execute_gcode("M109 S123")
    """ we expect a call to M104, followed by a call to M116 """
    m114 = self.mock_execute.call_args_list[0][0][0].message
    self.assertEqual(m114, "M104 S123")

    m116 = self.mock_execute.call_args_list[1][0][0].message
    self.assertEqual(m116, "M116 P0")

  def test_gcodes_M109_T2_S234(self):
    self.execute_gcode("M109 T2 S234")

    m114 = self.mock_execute.call_args_list[0][0][0].message
    self.assertEqual(m114, "M104 T2 S234")

    m116 = self.mock_execute.call_args_list[1][0][0].message
    self.assertEqual(m116, "M116 T2 S234")    # S234 is redundant and does no harm. Let it be.
