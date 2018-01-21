from __future__ import absolute_import

import mock
from random import random

from .MockPrinter import MockPrinter
from redeem.Gcode import Gcode


class M114_Tests(MockPrinter):

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
        self.printer.path_planner.get_current_pos.assert_called_with(ideal=True, mm=True)  # kinda redundant, but hey.

        self.assertEqual(g.answer,
                         "ok C: X:{:.1f} Y:{:.1f} Z:{:.1f} E:{:.1f} A:{:.1f} B:{:.1f} C:{:.1f} H:{:.1f}".format(
                             X, Y, Z, E, A, B, C, H
                         ))

