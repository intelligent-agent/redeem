"""
GCode M562

Example: M562 P0 

Reset temperature fault

Author: Elias Bakken
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import numpy as np
import logging
from six import iteritems


class M562(GCodeCommand):

    def execute(self, g):
        if g.has_letter("P"):
            heater_nr = g.get_int_by_letter("P", 1)
            if P == 0:
                self.printer.heaters["HBP"].extruder_error = False
            elif P == 1:
                self.printer.heaters["E"].extruder_error = False
            elif P == 2:
                self.printer.heaters["H"].extruder_error = False
        else: # No P, Enable all heaters
            for _, heater in iteritems(self.printer.heaters):
                heater.extruder_error = False

    def get_description(self):
        return "Reset temperature fault. "
    
    def get_long_description(self):
        return ("Reset a temperature fault on heater/sensor "
                "If the priner has switched off and locked a heater "
                "because it has detected a fault, this will reset the "
                "fault condition and allow you to use the heater again. "
                "Obviously to be used with caution. If the fault persists "
                "it will lock out again after you have issued this command. "
                "P0 is the bed; P1 the first extruder, and so on. ")
