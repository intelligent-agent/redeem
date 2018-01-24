"""
GCode M105
Get extruder temperature

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

import math
from six import iteritems
import logging
from .GCodeCommand import GCodeCommand


class M105(GCodeCommand):

    def execute(self, g):

        def format_temperature(heater, prefix):
            """
            Returns <prefix>:<heater temperature> for a given heater and
            prefix. Temperature values are formatted as integers.
            """
            temp =   self.printer.heaters[heater].get_temperature()
            target = self.printer.heaters[heater].get_target_temperature()
            return "{0}:{1:.1f}/{2:.1f}".format(prefix, temp, target)

        # Cura expects the temperature from the first
        current_tool = self.printer.current_tool
        answer = "ok " + format_temperature(current_tool, "T")

        # Append heaters
        for heater, data in sorted(iteritems(self.printer.heaters), key=lambda(k, v): (v, k)):
            answer += " " + format_temperature(heater, data.prefix)

            # Append the current tool power
            current_power = math.floor(255*self.printer.heaters[current_tool].mosfet.get_power())
            if current_power > 0.0:
                answer += " @:" + str(current_power)

        for c, cooler in enumerate(self.printer.cold_ends):
            temp = cooler.get_temperature()
            answer += " C{0}:{1:.0f}".format(c, temp)
   
        #logging.info(answer)
        g.set_answer(answer)

    def get_description(self):
        return "Get extruder temperature"

    def get_long_description(self):
        return ("Gets the current extruder temperatures, power "
                "and cold end temperatures.  "
                "Extruders have prefix T, cold endsa have prefix C, "
                "power has prefix @")


    def is_buffered(self):
        return False
