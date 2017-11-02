"""
GCode M151 - Enable min temperature alarm

Example: M151

Author: Elias Bakken
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import logging
from six import iteritems


class M151(GCodeCommand):

    def execute(self, g):
        for _, heater in iteritems(self.printer.heaters):
            heater.enable_min_temp()

    def get_description(self):
        return "Enable min temperature alarm"
    
    def get_long_description(self):
        return ("Should be enabled after target temperatures have been reached, "
                "typically after an M116 G-code or similar. Once enabled, if the "
                "temperature drops below the set point, the print will stop and "
                "all heaters will be disabled. The min temp will be disabled once "
                "a new temperture is set. Example: M151")
