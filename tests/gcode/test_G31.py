from __future__ import absolute_import

from .MockPrinter import MockPrinter
from Gcode import Gcode
import unittest
import mock

class G31_Tests(MockPrinter):

    def test_G31_is_buffered(self):
        g = Gcode({"message": "G31"})
        self.assertTrue(self.printer.processor.is_buffered(g))

    @mock.patch("gcodes.G31.Gcode")
    def test_G31_runs_macro(self, mock_Gcode):
        self.printer.processor.execute = mock.Mock() # prevent macro command execution
        macro_gcodes = self.printer.config.get("Macros", "G31").split("\n")

        self.execute_gcode("G31")
        """ compare macro from config, to macro commands executed """
        for i, v in enumerate(macro_gcodes):
            self.assertEqual(v, mock_Gcode.call_args_list[i][0][0]["message"])
