from __future__ import absolute_import

from .MockPrinter import MockPrinter
from numpy.testing import assert_array_equal
import mock


class M92_Tests(MockPrinter):
  def setUp(self):
    self.steps_pr_mm = {}

    for axis, stepper in self.printer.steppers.items():
      self.steps_pr_mm[axis] = stepper.steps_pr_mm
      stepper.set_microstepping(0)

    self.printer.path_planner.update_steps_pr_meter = mock.Mock()

  def _check_microsteps_pr_meter(self):
    # to make the test output easier to read, we actually convert from meters to millimeters
    printer_microsteps = [val / 1000.0 for val in self.printer.get_steps_pr_meter()]
    expected_microsteps = [
        self.steps_pr_mm[self.printer.index_to_axis(axis_num)]
        for axis_num in range(self.printer.num_axes)
    ]

    assert_array_equal(expected_microsteps, printer_microsteps)

  def test_gcodes_M92_noop(self):
    self.printer.path_planner.update_steps_pr_meter.assert_not_called()
    self._check_microsteps_pr_meter()
    self.execute_gcode("M92")
    self._check_microsteps_pr_meter()
    self.printer.path_planner.update_steps_pr_meter.assert_called_once()

  def test_gcodes_M92_X5_Z200_H50000(self):
    self.execute_gcode("M92 X5 Z200.0 H50000.0000")
    self.steps_pr_mm['X'] = 5.0
    self.steps_pr_mm['Z'] = 200.0
    self.steps_pr_mm['H'] = 50000.0
    self._check_microsteps_pr_meter()
    self.printer.path_planner.update_steps_pr_meter.assert_called_once()

  def test_gcodes_M92_E0_001_H0_0050(self):
    self.execute_gcode("M92 E0.001 H0.0050")
    self.steps_pr_mm['E'] = 0.001
    self.steps_pr_mm['H'] = 0.0050
    self._check_microsteps_pr_meter()
    self.printer.path_planner.update_steps_pr_meter.assert_called_once()

  def test_gcodes_M92_Yneg_Zneg(self):
    self.execute_gcode("M92 Y-0.05 Z-2")
    # should be a no-op
    self._check_microsteps_pr_meter()
    self.printer.path_planner.update_steps_pr_meter.assert_called_once()

  def test_gcodes_M92_Xneg_Y8_44(self):
    self.execute_gcode("M92 X-22 Y8.44")
    # negative X is ignored
    self.steps_pr_mm['Y'] = 8.44
    self._check_microsteps_pr_meter()
    self.printer.path_planner.update_steps_pr_meter.assert_called_once()
