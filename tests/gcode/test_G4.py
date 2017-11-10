from __future__ import absolute_import

from .MockPrinter import MockPrinter
from Gcode import Gcode
import unittest
import mock

class G4_Tests(MockPrinter):

    def test_G4_is_buffered(self):
        g = Gcode({"message": "G4"})
        self.assertTrue(self.printer.processor.is_buffered(g))

    @mock.patch('time.sleep')
    def test_G4_milliseconds(self, mock_time):
        self.execute_gcode("G4 P1234")
        mock_time.assert_called_with(1.234)

    @mock.patch('time.sleep')
    def test_G4_seconds(self, mock_time):
        self.execute_gcode("G4 S1.234")
        mock_time.assert_called_with(1.234)
