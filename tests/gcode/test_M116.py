from __future__ import absolute_import

import mock
import logging
from .MockPrinter import MockPrinter

logging.info = mock.Mock()


def mock_sleep(t):
  global heaters
  for heater in heaters:
    if mock_sleep.counter == list(heaters.keys()).index(heater) * 3:
      print("{:04d}: Heater {} target reached".format(mock_sleep.counter, heater))
      heaters[heater].is_target_temperature_reached.return_value = True
  mock_sleep.counter += 1
  return None


class M116_Tests(MockPrinter):
  def reset(self):
    for heater in self.printer.heaters:
      self.printer.heaters[heater] = mock.Mock()
      self.printer.heaters[heater].is_target_temperature_reached = mock.Mock(return_value=False)
    mock_sleep.counter = -3

  def setUp(self):
    global heaters
    heaters = self.printer.heaters
    self.reset()
    self.printer.processor.execute = mock.Mock()    # mock M116's call to M105

  @mock.patch("redeem.gcodes.M116.time.sleep", side_effect=mock_sleep)
  def test_gcodes_M116_no_param(self, m):
    print("")
    self.execute_gcode("M116")
    for heater in heaters:
      self.assertTrue(heaters[heater].is_target_temperature_reached())

  @mock.patch("redeem.gcodes.M116.time.sleep", side_effect=mock_sleep)
  def test_gcodes_M116_Pn_Tn(self, m):

    print("HEATERS: ", heaters)

    heater_index_order = [
        'HBP',
        'E',
        'H',
    ]

    for pt in ["P", "T"]:
      for heater in heater_index_order:
        heater_index = heater_index_order.index(heater) - 1
        self.reset()
        g = "M116 {}{}".format(pt, heater_index)
        print("\nGCODE: ", g)
        self.execute_gcode(g)

        print("Heater {} target reached: {} ".format(
            heater, heaters[heater].is_target_temperature_reached()))
        self.assertTrue(heaters[heater].is_target_temperature_reached())
