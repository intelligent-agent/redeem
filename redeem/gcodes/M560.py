"""
M560: Set or get stepper capabilities

Example: M560

Author: Elias Bakken
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

import os
import logging

from .GCodeCommand import GCodeCommand


class M560(GCodeCommand):

    def execute(self, g):
        if g.num_tokens() == 0:
            g.set_answer("ok "+", ".join([stepper.get_capabilities() for name,stepper in sorted(self.printer.steppers.iteritems())]))            
        else:
            answer = "ok "
            for i in range(g.num_tokens()):  # Run through all tokens
                axis = g.token_letter(i)
                value = int(g.token_value(i))
                if not axis in self.printer.steppers:
                    logging.warning("M560: Invalid axis key: %s", axis)
                    return
                answer += self.printer.steppers[axis].get_capabilities()
            g.set_answer(answer)
           
    def get_description(self):
        return "Set or get stepper capabilities"

    def get_long_description(self):
        return ("Set the direction for each axis. ")

