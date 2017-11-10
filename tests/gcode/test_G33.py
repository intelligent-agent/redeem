from __future__ import absolute_import

from .MockPrinter import MockPrinter
import mock
from testfixtures import Comparison as C
from Path import Path
from Gcode import Gcode
import numpy as np

class G33_Tests(MockPrinter):

    def setUp(self):
        pass
        
    def test_G33_is_buffered(self):
        g = Gcode({"message": "G33"})
        self.assertTrue(self.printer.processor.is_buffered(g))

    @mock.patch("gcodes.G33.Gcode")
    def test_G33_abort_on_bad_factor_count(self, mock_Gcode):
        bad_factor_nums = [-1,0,1,2,5,7,10]
        for f in bad_factor_nums:
            self.execute_gcode("G33 N"+str(f))

        mock_Gcode.assert_not_called()
        
    @mock.patch("gcodes.G33.Gcode")
    def test_gcodes_G33_runs_G29_macro(self, mock_Gcode):

        self.printer.processor.execute = mock.Mock() # prevent macro command execution
        macro_gcodes = self.printer.config.get("Macros", "G29").split("\n")

        self.execute_gcode("G33 N3")
        """ compare macro from config, to macro commands created using Gcode() inside G33.execute """
        for i, v in enumerate(macro_gcodes):
            self.assertEqual(v, mock_Gcode.call_args_list[i][0][0]["message"])

    def test_gcodes_G33_correct_args_to_autocalibrate_delta_printer(self):
        offset_z = self.printer.config.set('Probe', 'offset_z', str(-0.0012)) # arbitrary probe offset, -1.2mm
        self.printer.probe_points = [ # roughly 120 degree equalateral triangle, 30mm off the deck
                { 0.080,    0.0, 0.030},
                {-0.040,  0.070, 0.030},
                {-0.040, -0.070, 0.030}
            ]
        self.printer.probe_heights = [0.031, 0.032, 0.033] # imoderate (arbitrary) build plate angle

        self.printer.processor.execute = mock.Mock() # prevent macro command execution
        self.printer.path_planner.autocalibrate_delta_printer= mock.Mock()

        self.execute_gcode("G33 N3")

        """ retrieve args passed to autocalibrate_delta_printer and compare to expected """
        autocal_call_args = self.printer.path_planner.autocalibrate_delta_printer.call_args[0]
        self.assertEqual(autocal_call_args[0], 3)
        self.assertEqual(autocal_call_args[1], False)
        np.testing.assert_array_equal(
                autocal_call_args[2],
                np.array([ 
                    set([0.0, 0.03, 0.08]), 
                    set([-0.04, 0.070, 0.03]), 
                    set([-0.04, -0.070, 0.03])
                ])
            )
        np.testing.assert_array_equal(
                np.round(autocal_call_args[3], 3),
                np.array([ 1.231,  1.232,  1.233])
            )
