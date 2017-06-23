from MockPrinter import MockPrinter
import mock
from testfixtures import Comparison as C
from Path import Path
from Gcode import Gcode

class G33_Tests(MockPrinter):

    def setUp(self):
        pass
        
    def test_G33_is_buffered(self):
        g = Gcode({"message": "G30"})
        self.assertTrue(self.printer.processor.is_buffered(g))

    @mock.patch("gcodes.G33.Gcode")
    def test_G33_abort_on_bad_factor_count(self, mock_Gcode):
        bad_factor_nums = [-1,0,1,2,5,7,10]
        for f in bad_factor_nums:
            self.execute_gcode("G33 N"+str(f))

        mock_Gcode.assert_not_called()
        
    @mock.patch("gcodes.G33.Gcode")
    def test_gcodes__G33_runs_G29_macro(self, mock_Gcode):

        self.printer.processor.execute = mock.Mock() # prevent macro command execution
        macro_gcodes = self.printer.config.get("Macros", "G29").split("\n")

        self.execute_gcode("G33 N4")
        """ compare macro from config, to macro commands created using Gcode() inside G33.execute """
        for i, v in enumerate(macro_gcodes):
            self.assertEqual(v, mock_Gcode.call_args_list[i][0][0]["message"])

        # TODO: More tests for G33
