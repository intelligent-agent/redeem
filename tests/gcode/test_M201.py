from __future__ import absolute_import

from .MockPrinter import MockPrinter
import mock
from random import random


class M201_Tests(MockPrinter):
  def setUp(self):
    self.printer.path_planner.native_planner.setAcceleration = mock.Mock()
    self.printer.axis_config = self.printer.AXIS_CONFIG_XY
    self.printer.speed_factor = 1.0

  def exercise(self):
    values = {}
    gcode = "M201"
    for i, v in enumerate(self.printer.acceleration):
      axis = self.printer.AXES[i]
      values[axis] = round(random() * 9000.0, 0)
      gcode += " {:s}{:.0f}".format(axis, values[axis])

    self.execute_gcode(gcode)
    return {
        "values": values,
        "call_args": self.printer.path_planner.native_planner.setAcceleration.call_args[0][0]
    }

  def test_gcodes_M201_all_axes_G21_mm(self):
    test_data = self.exercise()
    for i, axis in enumerate(self.printer.AXES):
      expected = round(test_data["values"][axis] * self.printer.factor / 3600.0, 4)
      result = test_data["call_args"][i]
      self.assertEqual(expected, result,
                       axis + ": expected {:.0f} but got {:.0f}".format(expected, result))

  def test_gcodes_M201_all_axes_G20_inches(self):
    self.printer.factor = 25.4
    test_data = self.exercise()
    for i, axis in enumerate(self.printer.AXES):
      expected = round(test_data["values"][axis] * self.printer.factor / 3600.0, 4)
      result = test_data["call_args"][i]
      self.assertEqual(expected, result,
                       axis + ": expected {:.0f} but got {:.0f}".format(expected, result))

  def test_gcodes_M201_CoreXY(self):
    self.printer.axis_config = self.printer.AXIS_CONFIG_CORE_XY

    while True:    # account for remote possibility of two equal random numbers for X and Y
      test_data = self.exercise()
      if test_data["values"]["X"] != test_data["values"]["Y"]:
        break

    self.assertEqual(
        test_data["call_args"][0], test_data["call_args"][1],
        "For CoreXY mechanics, X & Y values must match. But X={}, Y={} (mm/min / 3600)".format(
            test_data["call_args"][0], test_data["call_args"][1]))

  def test_gcodes_M201_H_belt(self):
    self.printer.axis_config = self.printer.AXIS_CONFIG_H_BELT

    while True:    # account for remote possibility of two equal random numbers for X and Y
      test_data = self.exercise()
      if test_data["values"]["X"] != test_data["values"]["Y"]:
        break

    self.assertEqual(
        test_data["call_args"][0], test_data["call_args"][1],
        "For H-Belt mechanics, X & Y values must match. But X={}, Y={} (mm/min / 3600)".format(
            test_data["call_args"][0], test_data["call_args"][1]))

  def test_gcodes_M201_Delta(self):
    self.printer.axis_config = self.printer.AXIS_CONFIG_DELTA

    while True:    # account for super, ultra-duper remote possibility of three equal random numbers for X , Y and Z
      test_data = self.exercise()
      if (test_data["values"]["X"] + test_data["values"]["Y"] + test_data["values"]["Y"]) != (
          test_data["values"]["X"] * 3):
        break

    self.assertEqual(
        test_data["call_args"][0] + test_data["call_args"][1] + test_data["call_args"][2],
        test_data["call_args"][0] * 3,
        "For CoreXY mechanics, X & Y values must match. But X={}, Y={} (mm/min / 3600)".format(
            test_data["call_args"][0], test_data["call_args"][1], test_data["call_args"][2]))
