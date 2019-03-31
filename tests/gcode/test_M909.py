from __future__ import absolute_import

from .MockPrinter import MockPrinter
from numpy.testing import assert_array_equal
import numpy
import mock


class M909_Tests(MockPrinter):
  def setUp(self):
    self.steps_pr_mm = {}
    self.microstep_configs = {}

    for axis, stepper in self.printer.steppers.items():
      self.steps_pr_mm[axis] = stepper.steps_pr_mm
      self.microstep_configs[axis] = stepper.microstepping

    self.printer.path_planner.update_steps_pr_meter = mock.Mock()

  def _check_microsteps_pr_meter(self):
    # first we check just the microstep configs because this makes failures easier to diagnose
    printer_microstep_configs = numpy.ones(self.printer.num_axes)
    expected_microstep_configs = numpy.ones(self.printer.num_axes)
    for axis, stepper in self.printer.steppers.items():
      index = self.printer.axis_to_index(axis)
      printer_microstep_configs[index] = stepper.microstepping
      expected_microstep_configs[index] = self.microstep_configs[axis]

    assert_array_equal(expected_microstep_configs, printer_microstep_configs)

    # next check the final multiplied microsteps per mm
    printer_microsteps = [val / 1000.0 for val in self.printer.get_steps_pr_meter()]
    expected_microsteps = []

    for axis_num in range(self.printer.num_axes):
      axis = self.printer.index_to_axis(axis_num)
      expected_microsteps.append(self.steps_pr_mm[axis] *
                                 self.microstep_config_to_multiplier[self.microstep_configs[axis]])

    assert_array_equal(expected_microsteps, printer_microsteps)

  def test_gcodes_M909_noop(self):
    self.printer.path_planner.update_steps_pr_meter.assert_not_called()
    self._check_microsteps_pr_meter()
    self.execute_gcode("M909")
    self._check_microsteps_pr_meter()
    self.printer.path_planner.update_steps_pr_meter.assert_called_once()

  def test_gcodes_M909_X0_Y1_E2(self):
    self.execute_gcode("M909 X0 Y1 E2")
    self.microstep_configs['X'] = 0
    self.microstep_configs['Y'] = 1
    self.microstep_configs['E'] = 2
    self._check_microsteps_pr_meter()
    self.printer.path_planner.update_steps_pr_meter.assert_called_once()

  def test_gcodes_M909_H5_E4_Z2(self):
    self.execute_gcode("M909 H5 E4 Z2")
    self.microstep_configs['H'] = 5
    self.microstep_configs['E'] = 4
    self.microstep_configs['Z'] = 2
    self._check_microsteps_pr_meter()
    self.printer.path_planner.update_steps_pr_meter.assert_called_once()

  def test_gcodes_M909_X20(self):
    self.execute_gcode("M909 X20")
    # should be a no-op
    self._check_microsteps_pr_meter()
    self.printer.path_planner.update_steps_pr_meter.assert_called_once()

  def test_gcodes_M909_Xneg(self):
    self.execute_gcode("M909 X-1")
    # should be a no-op
    self._check_microsteps_pr_meter()
    self.printer.path_planner.update_steps_pr_meter.assert_called_once()
