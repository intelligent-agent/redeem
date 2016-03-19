"""
GCode M910
Set stepper decay mode

Author: Elias Bakken
email: elias at iagent dot no
Website: http://www.thing-printer.com
License: GPLv3
"""

from GCodeCommand import GCodeCommand
import logging

class M910(GCodeCommand):

    def execute(self, g):
        for i in range(g.num_tokens()):
            self.printer.steppers[g.token_letter(i)].set_decay(int(g.token_value(i)))

    def get_description(self):
        return "Set stepper controller decay mode"

    def get_long_description(self):
        return ("Example: M910 X3 Y5 Z2 E3"
                "Set the decay mode for"
                "each of the steppers. In Redeem this is implemented"
                "for Replicape rev B as a combination of CFG0, CFG4, CFG5."
                "A value between 0 and 7 is allowed, setting the three "
                "registers to the binary value represented by CFG0, CFG4, CFG5.\n"
                "CFG0 is chopper off time, the duration of slow decay phase.\n"
                "CFG4 is chopper hysteresis, the tuning of zero crossing precision.\n"
                "CFG5 is the chopper blank time, the dureation of banking of switching spike.\n"
                "Please refer to the data sheet for further details on the configs. ")

 
