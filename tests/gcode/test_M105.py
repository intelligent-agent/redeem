from MockPrinter import MockPrinter
import mock
from Gcode import Gcode
from random import random
import math
from six import iteritems


class M105_Tests(MockPrinter):

    def test_gcodes_M105(self):
        test_temps = {}
        test_target_temps = {}
        for n in self.printer.heaters:
            prefix = self.printer.heaters[n].prefix
            test_temps[prefix] = round(random()*100, 2)
            test_target_temps[prefix] = round(random()*100, 2)
            self.printer.heaters[n].get_temperature = mock.Mock(return_value = test_temps[prefix])
            self.printer.heaters[n].get_target_temperature = mock.Mock(return_value = test_target_temps[prefix])

        g = Gcode({"message": "M105"})
        self.printer.processor.gcodes[g.gcode].execute(g)
        
        expected_answer = "ok"
        expected_answer += " {0}:{1:.1f}/{2:.1f}".format("T", test_temps["T0"], test_target_temps["T0"])

        for heater, data in sorted(iteritems(self.printer.heaters), key=lambda(k,v): (v,k)):
            p = data.prefix
            expected_answer += " {0}:{1:.1f}/{2:.1f}".format(p, test_temps[p], test_target_temps[p])
        expected_answer += " @:0.0" # mosfet power unavailable due to test mocking. meh.

        self.assertEqual(g.answer, expected_answer)





