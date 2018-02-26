"""
GCode M558 
Author: Elias Bakken
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

import logging
from .GCodeCommand import GCodeCommand


class M558(GCodeCommand):

    def execute(self, g):
        if g.has_letter("P"):
            t = g.get_int_by_letter("P")
        else:
            logging.warning("M558: Missing P-parameter")
            return         
        if t not in [0]: # TODO: Add more, at least proximity sensor
            logging.warning("M558: Wrong probe type. Use 0 - Servo with switch")
            return         
        self.printer.probe_type = t

    def get_description(self):
        return "Set probe type"

    def get_long_description(self):
        return(
            "Example: M558 P0 \n"
            "where P can be\n"
            "  0 - Servo with Switch \n"
            "  1 - IR \n"
            "  2 - IR \n"
            "  3 - Proximity sensor\n \n"
            "A Z probe may be a switch (the default) an IR proximity sensor, or some other \n"
            "device. This selects which to use. P0 gives a switch. P1 gives an unmodulated \n"
            "IR probe, or any other probe type that emulates an unmodulated IR probe (probe \n"
            "output is an analog signal that rises with decreasing nozzle height above \n"
            "the bed). If there is a control signal to the probe, it is driven high when \n"
            "the probe type is P1. P2 specifies a modulated IR probe, where the modulation \n"
            "is commanded directly by the main board firmware using the control signal to \n"
            "the probe. P3 selects an alternative Z probe by driving the control signal to \n"
            "the probe low. See also G31 and G32."
            )
