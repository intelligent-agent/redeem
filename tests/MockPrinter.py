import unittest
import mock

import sys
sys.path.insert(0, '../redeem')
sys.path.insert(0, './TestStubs')

from Printer import Printer
from USB import USB
from Path import Path, AbsolutePath, RelativePath, MixedPath
from PathPlanner import PathPlanner
from GCodeProcessor import GCodeProcessor
from Gcode import Gcode
from CascadingConfigParser import CascadingConfigParser

class MockPrinter(unittest.TestCase):

    AbsolutePath = AbsolutePath
    RelativePath = RelativePath
    MixedPath = MixedPath

    @classmethod
    def setUpClass(self):
        printer = Printer()
        self.printer = printer

        self.printer.path_planner = mock.create_autospec(PathPlanner)
        self.printer.send_message = mock.create_autospec(self.printer.send_message)
        self.printer.processor = GCodeProcessor(self.printer)
        self.printer.comms[0] = mock.create_autospec(USB)
        printer.config = CascadingConfigParser(['../configs/default.cfg'])
        printer.config.check('../configs/default.cfg')

        printer.movement == Path.ABSOLUTE
        printer.feed_rate = 0.050 # m/s
        printer.accel = 0.050 / 60 # m/s/s

        Gcode.printer = printer
        Path.printer = printer


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

