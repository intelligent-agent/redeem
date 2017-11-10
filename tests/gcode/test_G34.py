from __future__ import absolute_import

from .MockPrinter import MockPrinter
import mock
from testfixtures import Comparison as C
from Gcode import Gcode

class G34_Tests(MockPrinter):

    def setUp(self):
        self.printer.path_planner.get_current_pos = mock.Mock(
                autospec=True, 
                return_value={"X":10.0, "Y": 20.0, "Z":30.0}
            )
        self.printer.processor.execute = mock.Mock(autospec=True) # block gcode execution
        self.printer.path_planner.probe = mock.Mock(return_value=0.029)
        
    def test_G34_is_buffered(self):
        g = Gcode({"message": "G34"})
        self.assertTrue(self.printer.processor.is_buffered(g))

    @mock.patch("gcodes.G34.Gcode")
    def test_G34_expected_gcodes(self, mock_Gcode):
        self.printer.config.set = mock.Mock()
        self.execute_gcode("G34 Z10")

        """  check for Gcode moves to correct locations """
        gcode_calls = mock_Gcode.call_args_list
        expected_gcodes = [
                "G0 Z40.0",
                "G32",
                "G31"
            ]
        for i, v in enumerate(gcode_calls):
            self.assertEqual(v[0][0]["message"], expected_gcodes[i])

        self.printer.config.set.assert_called_with("Probe", "offset_z", "-0.001")
