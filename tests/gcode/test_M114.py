from MockPrinter import MockPrinter
import mock
from Gcode import Gcode
from random import random
import math
import logging

class M112_Tests(MockPrinter):

    def test_gcodes_M114(self):
        A = round(random()*200, 1)
        B = round(random()*200, 1)
        C = round(random()*200, 1)
        X = round(random()*200, 1)
        Y = round(random()*200, 1)
        Z = round(random()*200, 1)
        E = round(random()*200, 1)
        H = round(random()*200, 1)
        self.printer.path_planner.get_current_pos = mock.Mock(
                return_value = {
                    'A': A, 
                    'C': C, 
                    'B': B, 
                    'E': E, 
                    'H': H,
                    'Y': Y, 
                    'X': X, 
                    'Z': Z
                }
            )
        g = Gcode({"message": "M114"})
        self.printer.processor.gcodes[g.gcode].execute(g)
        self.printer.path_planner.get_current_pos.assert_called_with(mm=True)
        self.assertEqual(g.answer, 
                "ok C: X:{:.1f} Y:{:.1f} Z:{:.1f} E:{:.1f} A:{:.1f} B:{:.1f} C:{:.1f} H:{:.1f}".format(
                    X, Y, Z, E, A, B, C, H
            )
        )
  
