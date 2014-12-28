"""
GCode M558 
Example: M558 P0

0 - Servo with Switch
1 - IR
2 - IR
3 - Proximity sensor

A Z probe may be a switch (the default) an IR proximity sensor, or some other device. This selects which to use. P0 gives a switch. P1 gives an unmodulated IR probe, or any other probe type that emulates an unmodulated IR probe (probe output is an analog signal that rises with decreasing nozzle height above the bed). If there is a control signal to the probe, it is driven high when the probe type is P1. P2 specifies a modulated IR probe, where the modulation is commanded directly by the main board firmware using the control signal to the probe. P3 selects an alternative Z probe by driving the control signal to the probe low. See also G31 and G32. 

Author: Elias Bakken
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import logging


class M558(GCodeCommand):

    def execute(self, g):
        if g.has_letter("P"):
            t = int(g.get_value_by_letter("P"))
        else:
            logging.warning("M558: Missing P-parameter")
            return         
        if t not in [0]: # TODO: Add more, at least proximity sensor
            logging.warning("M558: Wrong probe type. Use 0 - Servo with switch")
            return         
        self.printer.probe_type = t

    def get_description(self):
        return "Set probe type"
