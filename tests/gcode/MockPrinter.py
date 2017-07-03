import unittest
import mock
import os
import sys
sys.path.insert(0, '../redeem')
# sys.path.insert(0, './gcode/TestStubs')

sys.modules['EndStop'] = mock.Mock()
sys.modules['RotaryEncoder'] = mock.Mock()
sys.modules['Watchdog'] = mock.Mock()
sys.modules['GPIO'] = mock.Mock()
sys.modules['Enable'] = mock.Mock()
sys.modules['Key_pin'] = mock.Mock()
sys.modules['GPIO'] = mock.Mock()
sys.modules['Adafruit_BBIO'] = mock.Mock()
sys.modules['Adafruit_BBIO.GPIO'] = mock.Mock()
sys.modules['StepperWatchdog'] = mock.Mock()
sys.modules['StepperWatchdog.GPIO'] = mock.Mock()
sys.modules['_PathPlannerNative'] = mock.Mock()
sys.modules['PruInterface'] = mock.Mock()
sys.modules['PruFirmware'] = mock.Mock()
sys.modules['Extruder'] = mock.Mock()
sys.modules['HBD'] = mock.Mock()
sys.modules['Fan'] = mock.Mock()
sys.modules['RotaryEncoder'] = mock.Mock()
sys.modules['JoinableQueue'] = mock.Mock()
sys.modules['USB'] = mock.Mock()
sys.modules['Ethernet'] = mock.Mock()
sys.modules['Pipe'] = mock.Mock()
from Redeem import *

"""
MockPrinter, in combination with the many sys.module[...] = Mock() statements
above, creates a mock Redeem instance. The mock instance has only what is
needed for our tests and does not access any BBB hardware IOs.
"""
class MockPrinter(unittest.TestCase):

    @classmethod
    def setUpClass(self):

        tmp_local_cfg = open("../configs/local.cfg", "w")
        tmp_local_cfg.write("[System]\nlog_to_file = False\n")
        tmp_local_cfg.close()

        self.R = Redeem("../configs")
        printer = self.printer = self.R.printer

        self.printer.path_planner = mock.MagicMock()
        self.gcodes = self.printer.processor.gcodes
        self.printer.send_message = mock.create_autospec(self.printer.send_message)

        self.printer.movement = Path.ABSOLUTE
        self.printer.feed_rate = 0.050 # m/s
        self.printer.accel = 0.050 / 60 # m/s/s

        Gcode.printer = printer
        Path.printer = printer

        """ 
        We want to ensure that printer.factor is always obeyed correctly
        For convenience, we'll set it to mm/inch and check that resulting 
        paths have the correct meter values, converted from inch input.
        """
        self.printer.factor = self.f = 25.4 # inches

        self.printer.probe_points = []
        self.printer.replicape_key = "DUMMY_KEY"

    @classmethod
    def tearDownClass(self):
        self.R = self.printer = None
        os.remove("../configs/local.cfg")
        pass

    """ directly calls a Gcode class's execute method, bypassing printer.processor.execute """
    def execute_gcode(self, text):
        g = Gcode({"message": text})
        return self.printer.processor.gcodes[g.gcode].execute(g)

    def fullpath(self, o):
      return o.__module__ + "." + o.__class__.__name__
