from __future__ import absolute_import

from .MockPrinter import MockPrinter
import mock
from testfixtures import Comparison as C
from Path import Path
from Gcode import Gcode

class G30_Tests(MockPrinter):

    def setUp(self):
        self.printer.path_planner.probe = mock.Mock(return_value=12.34 / 1000)
        self.printer.path_planner.get_current_pos = mock.Mock(return_value={"X": 10.0, "Y": 20.0, "Z": 35.0})
        
        """ set known offsets for X and Y, both here and within G30.execute """
        self.printer.config.getfloat = mock.Mock(return_value=11.22)
        self.offset_x = self.printer.config.getfloat('Probe', 'offset_x')*1000
        self.offset_y = self.printer.config.getfloat('Probe', 'offset_y')*1000

        self.printer.probe_points = [
                {"X":10.0, "Y":20.0, "Z":30.0},
                {"X":11.0, "Y":22.0, "Z":33.0}
            ]
        self.printer.probe_heights = [0, 0]

    def test_G30_is_buffered(self):
        g = Gcode({"message": "G30"})
        self.assertTrue(self.printer.processor.is_buffered(g))

    @mock.patch("gcodes.G30.Gcode") 
    def test_gcodes_G30_point_0_not_set(self, mock_Gcode):
        self.printer.probe_points = []
        self.execute_gcode("G30 P0") # should abort because there is no P0 point stored yet (M557)
        self.assertFalse(mock_Gcode.called)

    @mock.patch("gcodes.G30.Gcode") 
    def test_gcodes_G30_X_Y_Z_speed_accel(self, mock_Gcode):
        self.execute_gcode("G30 X10 Y20 Z35 D10.0 F3000 Q1000")
        expected_moveto = "G0 X{} Y{} Z{}".format(10.0+self.offset_x, 20.0+self.offset_y, 35.0) 
        gcode_packet = mock_Gcode.call_args[0][0]
        self.assertEqual(expected_moveto, gcode_packet["message"])
        self.printer.path_planner.probe.assert_called_with(
                10.0 / 1000,        # D10.0 (probe height)
                3000.0 / 60000,     # F3000 (speed)
                1000.0 / 3600000    # Q1000 (acceration)
            )

    def test_gcodes_G30_S_but_no_P(self):
        self.printer.probe_heights = [0]
        self.execute_gcode("G30 X10 Y10 Z10 S")
        self.printer.path_planner.probe.assert_called()
        self.assertEqual(self.printer.probe_heights[0], 0)

    def test_gcodes_G30_S_with_P(self):
        self.execute_gcode("G30 P1 S")
        self.printer.path_planner.probe.assert_called()
        self.assertEqual(self.printer.probe_heights[1], 12.34)
