"""
GCode M140
Set heated bed temperature

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

import logging
from .GCodeCommand import GCodeCommand


class M140(GCodeCommand):

    def execute(self, g):
        temperature = g.get_float_by_letter("S", 0.0)
        logging.debug("Setting bed temperature to %.1f", temperature)
        self.printer.heaters['HBP'].set_target_temperature(temperature)

    def get_description(self):
        return "Set heated bed temperature"

    def is_buffered(self):
        return True
