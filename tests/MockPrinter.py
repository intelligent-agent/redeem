import unittest
import mock

import sys
sys.path.insert(0, '../redeem')

from Printer import Printer
from USB import USB
from Path import Path, AbsolutePath, RelativePath, MixedPath, G92Path
from PathPlanner import PathPlanner
from GCodeProcessor import GCodeProcessor
from Gcode import Gcode

class MockPrinter(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.printer = Printer()
        self.printer.movement == Path.ABSOLUTE
        self.printer.feed_rate = 0.050 # m/s
        self.printer.accel = 0.050 / 60 # m/s/s
        
        Gcode.printer = self.printer
        Path.printer = self.printer

        self.mock_path_planner = mock.create_autospec(PathPlanner)
        self.printer.path_planner = self.mock_path_planner
        self.printer.processor = GCodeProcessor(self.printer)
        self.printer.comms[0] = mock.create_autospec(USB)

        """ 
        We want to ensure that printer.factor is always obeyed correctly
        For convenience, we'll set it to mm/inch and check that resulting 
        paths have the correct meter values.
        """
        self.printer.factor = self.f = 25.4 # inches

        self.GP = GCodeProcessor(self.printer)

    def execute_gcode(self, gcode):
        gcode = Gcode({"message": gcode})
        self.GP.execute(gcode)

