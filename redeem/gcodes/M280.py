"""
GCode M280 
Set servo position absolute. P: servo index, S: angle

Author: Elias Bakken
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

import logging
from .GCodeCommand import GCodeCommand


class M280(GCodeCommand):

    def execute(self, g):
        if g.has_letter("S"): # Angle
            angle = g.get_int_by_letter("S")
        else:
            logging.warning("M280: Missing S-parameter")
            return 
        if g.has_letter("P"):
            index = g.get_int_by_letter("P")
        else:
            logging.warning("M280: Missing P-parameter")
            return 
        if g.has_letter("F"):
            speed = g.get_float_by_letter("F")
        else:
            speed = 100
        # If "R" is present, be synchronous
        if g.has_letter("R"):
            async = False
        else:
            async = True
        # Index of servo
        if index < len(self.printer.servos):
            servo = self.printer.servos[index]
            servo.set_angle(angle, speed, async) 
        else:
            logging.warning("M280: Servo index out of range "+str(index))

    def is_buffered(self):
        return True

    def get_description(self):
        return "Set servo position"

    def get_long_description(self):
        return "Set servo position. Use 'S' to specify angle, use 'P' to specify index, use F to specify speed. "
