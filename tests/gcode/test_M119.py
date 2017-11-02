from MockPrinter import MockPrinter
import mock
from six import iteritems


class M119_Tests(MockPrinter):

    def setUp(self):
        i = 0
        for _,v in sorted(iteritems(self.printer.end_stops)):
            v.hit = ((i % 2) == 0)
            i += 1

    def test_gcodes_M119_no_args(self):
        g = self.execute_gcode("M119")
        self.assertEqual(g.answer, "ok X1: True, X2: False, Y1: True, Y2: False, Z1: True, Z2: False") 

    def test_gcodes_M119_X2_S1(self):
        self.printer.config.set = mock.Mock()
        self.printer.path_planner.pru_firmware.produce_firmware = mock.Mock()
        self.printer.config.save = mock.Mock()
        self.printer.path_planner.restart = mock.Mock()

        for state in range(0,1):
            for _,v in sorted(iteritems(self.printer.end_stops)):
                es = v.name
                self.printer.end_stops[es].invert = state

                g = self.execute_gcode("M119 "+es+" S"+str(state))
                
                self.assertEqual(self.printer.end_stops[es].invert, state)
                self.printer.config.set.assert_called_with('Endstops', 'invert_'+es, 'True' if state else 'False')
                self.printer.config.save.assert_called()
                self.printer.path_planner.pru_firmware.produce_firmware.assert_called()
                self.printer.path_planner.restart.assert_called()

