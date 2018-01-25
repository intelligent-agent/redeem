"""
GCode M130 M131 and M132
Adjust PID settings

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

from .GCodeCommand import GCodeCommand


class M130(GCodeCommand):

    heaters = ["HBP", "E", "H", "A", "B", "C"]

    @classmethod
    def get_params(self, g):
        self.extr = g.get_int_by_letter("P", 0) + 1
        self.value = g.get_float_by_letter("S", 0.1)
 
    def execute(self, g):
        self.get_params(g)
        heater = self.printer.heaters[M130.heaters[self.extr]]
        control = heater.input
        try:
            control.Kp = self.value
        except:
            msg = "set Kp failed for {} of {}".format(control.name, heater.name)
            logging.warning("")
        
    def get_description(self):
        return "Set PID P-value, Format (M130 P0 S8.0)"

    def get_long_description(self):
        return "Set PID P-value, Format (M130 P0 S8.0), S<-1, 0, 1>"


class M131(M130):
    def execute(self, g):
        self.get_params(g)
        heater = self.printer.heaters[M131.heaters[self.extr]]
        control = heater.input
        try:
            control.Ti = self.value
        except:
            msg = "set Ti failed for {} of {}".format(control.name, heater.name)
            logging.warning("")

    def get_description(self):
        return "Set PID I-value, Format (M131 P0 S8.0)"

    def get_long_description(self):
        return "Set PID I-value, Format (M131 P0 S8.0)"


class M132(M130):
    def execute(self, g):
        self.get_params(g)
        heater = self.printer.heaters[M132.heaters[self.extr]]
        control = heater.input
        try:
            control.Td = self.value
        except:
            msg = "set Td failed for {} of {}".format(control.name, heater.name)
            logging.warning("")


    def get_description(self):
        return "Set PID D-value, Format (M132 P0 S8.0)"

    def get_long_description(self):
        return "Set PID D-value, Format (M132 P0 S8.0)"
