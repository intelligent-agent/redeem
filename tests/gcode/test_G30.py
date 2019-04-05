from __future__ import absolute_import

import mock
from .MockPrinter import MockPrinter
from redeem.Gcode import Gcode


class G30_Tests(MockPrinter):
  def setUp(self):
    self.printer.path_planner.get_current_pos = mock.Mock(return_value={
        "X": 10.0,
        "Y": 20.0,
        "Z": 35.0
    })
    """ set known probe config values for use both here and within G30.execute """
    self.printer.config.set('Probe', 'length', str(0.020))    # Probe length 20mm
    self.printer.config.set('Probe', 'offset_x', str(0.001122))    # Probe X offset of 11.22 mm
    self.printer.config.set('Probe', 'offset_y', str(0.001122))    # Probe Y offset of 11.22 mm
    self.printer.config.set('Probe', 'offset_z', str(0.004))    # Probe Z offset of 4 mm

    self.offset_x = self.printer.config.getfloat('Probe', 'offset_x') * 1000
    self.offset_y = self.printer.config.getfloat('Probe', 'offset_y') * 1000
    self.offset_z = self.printer.config.getfloat('Probe', 'offset_z') * 1000
    """ Mock the printers default probe distance return value """
    self.printer.path_planner.probe = mock.Mock(return_value=self.offset_z)

    self.printer.probe_points = [{
        "X": 10.0,
        "Y": 20.0,
        "Z": 30.0
    }, {
        "X": 11.0,
        "Y": 22.0,
        "Z": 33.0
    }]
    self.printer.probe_heights = [0, 0]

  def test_G30_properties(self):
    self.assertGcodeProperties("G30", is_buffered=True, is_async=True)

  @mock.patch("redeem.gcodes.G30.Gcode")
  def test_gcodes_G30_point_0_not_set(self, mock_Gcode):
    self.printer.probe_points = []
    self.execute_gcode("G30 P0")    # should abort because there is no P0 point stored yet (M557)
    self.assertFalse(mock_Gcode.called)

  @mock.patch("redeem.gcodes.G30.Gcode")
  def test_gcodes_G30_X_Y_Z_speed_accel(self, mock_Gcode):
    self.execute_gcode("G30 X10 Y20 Z35 D10.0 F3000 Q1000")
    expected_moveto = "G0 X{} Y{} Z{}".format(10.0 + self.offset_x, 20.0 + self.offset_y, 35.0)
    gcode_packet = mock_Gcode.call_args[0][0]
    self.assertEqual(expected_moveto, gcode_packet["message"])
    self.printer.path_planner.probe.assert_called_with(
        10.0 / 1000,    # D10.0 (probe height)
        3000.0 / 60000,    # F3000 (speed)
        1000.0 / 3600000    # Q1000 (acceration)
    )

  def test_gcodes_G30_S_but_no_P(self):
    """ Test using a probe offset_z of 0.0mm """
    self.printer.config.set('Probe', 'offset_z', str(0.000))    # Probe Z offset of 0 mm
    self.offset_z = self.printer.config.getfloat('Probe', 'offset_z') * 1000
    self.assertEqual(self.offset_z, 0.0)
    """ Mock the printers default probe distance return value """
    self.printer.path_planner.probe = mock.Mock(return_value=self.offset_z / 1000)
    self.printer.probe_heights = [123456789]
    self.execute_gcode("G30 X10 Y10 Z10 S")
    self.printer.path_planner.probe.assert_called()
    """ S but no P means the pobed point will not be saved. Verify probe height has not been changed """
    self.assertEqual(self.printer.probe_heights[0], 123456789)

  def test_gcodes_G30_S_but_no_P_w_offset(self):
    """ Test using a probe offset_z of 4.0mm """
    self.printer.config.set('Probe', 'offset_z', str(0.004))    # Probe Z offset of 4 mm
    self.offset_z = self.printer.config.getfloat('Probe', 'offset_z') * 1000
    self.assertEqual(self.offset_z, 4.0)
    """ Mock the printers default probe distance return value """
    self.printer.path_planner.probe = mock.Mock(return_value=self.offset_z / 1000)
    self.printer.probe_heights = [123456789]
    self.execute_gcode("G30 X10 Y10 Z10 S")
    self.printer.path_planner.probe.assert_called()
    """ S but no P means the pobed point will not be saved. Verify probe height has not been changed """
    self.assertEqual(self.printer.probe_heights[0], 123456789)

  def test_gcodes_G30_S_with_P(self):
    """ Test using a probe offset_z of 0.0mm """
    self.printer.config.set('Probe', 'offset_z', str(0.000))    # Probe Z offset of 0 mm
    self.offset_z = self.printer.config.getfloat('Probe', 'offset_z') * 1000
    self.assertEqual(self.offset_z, 0.0)
    """ Mock the printers default probe distance return value """
    self.printer.path_planner.probe = mock.Mock(return_value=self.offset_z / 1000)
    self.execute_gcode("G30 P1 S")
    self.printer.path_planner.probe.assert_called()
    self.assertEqual(self.printer.probe_heights[1], 0)

  def test_gcodes_G30_S_with_P_w_offset(self):
    """ Test using a probe offset_z of 4.0mm """
    self.printer.config.set('Probe', 'offset_z', str(0.004))    # Probe Z offset of 4 mm
    self.offset_z = self.printer.config.getfloat('Probe', 'offset_z') * 1000
    self.assertEqual(self.offset_z, 4.0)
    """ Mock the printers default probe distance return value """
    self.printer.path_planner.probe = mock.Mock(return_value=self.offset_z / 1000)
    self.execute_gcode("G30 P1 S")
    self.printer.path_planner.probe.assert_called()
    self.assertEqual(self.printer.probe_heights[1], 0)
