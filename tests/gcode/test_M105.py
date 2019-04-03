from __future__ import absolute_import

import mock
from random import random
import math
from six import iteritems
from .MockPrinter import MockPrinter
from redeem.Gcode import Gcode


class M105_Tests(MockPrinter):
  def test_gcodes_M105(self):
    test_temps = {}
    test_target_temps = {}
    test_powers = {}
    for n in self.printer.heaters:
      prefix = self.printer.heaters[n].prefix
      test_temps[prefix] = round(random() * 100, 2)
      test_target_temps[prefix] = round(random() * 100, 2)
      test_powers[prefix] = round(random(), 2)
      self.printer.heaters[n].get_temperature = mock.Mock(return_value=test_temps[prefix])
      self.printer.heaters[n].get_target_temperature = mock.Mock(
          return_value=test_target_temps[prefix])
      self.printer.heaters[n].mosfet = mock.Mock(
      )    # TODO why is this necessary? All the heaters seem to be sharing the same mosfet?
      self.printer.heaters[n].mosfet.get_power = mock.Mock(return_value=test_powers[prefix])

    g = Gcode({"message": "M105"})
    self.printer.processor.gcodes[g.gcode].execute(g)

    expected_answer = "ok"
    expected_answer += " {0}:{1:.1f}/{2:.1f}".format("T", test_temps["T0"], test_target_temps["T0"])

    for heater, data in sorted(iteritems(self.printer.heaters), key=lambda pair: pair[0]):
      p = data.prefix
      expected_answer += " {0}:{1:.1f}/{2:.1f}".format(p, test_temps[p], test_target_temps[p])
    expected_answer += " @:{0:.1f}".format(math.floor(test_powers["T0"] * 255.0))

    self.assertEqual(g.answer, expected_answer)
