from MockPrinter import MockPrinter
import mock
from Gcode import Gcode
from random import random
import math

class M105_Tests(MockPrinter):

    def test_gcodes_M105(self):
        test_temps = {}
        test_target_temps = {}
        print "XXXX:",self.printer.heaters
        for n in self.printer.heaters:
            prefix = self.printer.heaters[n].prefix
            test_temps[prefix] = round(random()*100, 2)
            test_target_temps[prefix] = round(random()*100, 2)
            self.printer.heaters[n].get_temperature = mock.Mock(return_value = test_temps[prefix])
            self.printer.heaters[n].get_target_temperature = mock.Mock(return_value = test_target_temps[prefix])

        g = Gcode({"message": "M105"})
        self.printer.processor.gcodes[g.gcode].execute(g)
        
        expected_answer = "ok"
        expected_answer += " {0}:{1:.1f}/{2:.1f}".format("T", test_temps["T1"], test_target_temps["T1"])

        for h in self.printer.heaters:
            prefix = self.printer.heaters[h].prefix
            expected_answer += " {0}:{1:.1f}/{2:.1f}".format(prefix, test_temps[prefix], test_target_temps[prefix])

        #        T1:64.0/30.2 T1:64.0/30.2 B:90.3/65.8"
        self.assertEqual(g.answer, expected_answer)





