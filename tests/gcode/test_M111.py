from __future__ import absolute_import

from .MockPrinter import MockPrinter
import mock
from Gcode import Gcode
from random import random
import math
import logging

class M111_Tests(MockPrinter):

    def setUp(self):
        self.logger = logging.getLogger()
        self.log_level = self.logger.level
        
    def tearDown(self):
        self.logger.setLevel(self.log_level)
    
    def test_gcodes_M111_no_param(self):
        self.execute_gcode("M111")
        self.tmp_log_level = self.logger.level
        self.assertEqual(self.logger.level, self.tmp_log_level) # no change expected
        
    def test_gcodes_M111_bad_param(self):
        self.execute_gcode("M111 S21")
        self.tmp_log_level = self.logger.level
        self.assertEqual(self.logger.level, self.tmp_log_level) # no change expected
    
    def test_gcodes_M111_S20(self):
        self.execute_gcode("M111 S10")
        self.assertEqual(self.logger.level, 10)
        if hasattr(self.printer, "redeem_logging_handler"):
            self.assertEqual(self.printer.redeem_logging_handler.level, 10)
