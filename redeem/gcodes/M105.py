"""
GCode M105
Get extruder temperature

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import math

class M105(GCodeCommand):

    def execute(self, g):

        def format_temperature(heater, prefix):
            """
            Returns <prefix>:<heater temperature> for a given heater and
            prefix. Temperature values are formatted as integers.
            """
            temperature = self.printer.heaters[heater].get_temperature()
            return "{0}:{1:.0f}".format(prefix, temperature)

        # Cura expects the temperature from the first
        current_tool = self.printer.current_tool
        answer = "ok " + format_temperature(current_tool, "T")

        # Append heaters
        for h in self.printer.heaters:
            prefix = self.printer.heaters[h].prefix
            answer += " " + format_temperature(h, prefix)

        # Append all other readings
        if "HBP" in self.printer.heaters:
            answer += " " + format_temperature("HBP", "B")
        if "E" in self.printer.heaters:
            answer += " " + format_temperature("E", "T0")

        # Append the current tool power is using PID
        if not self.printer.heaters[current_tool].onoff_control:
            answer += " @:" + str(math.floor(255*self.printer.heaters[current_tool].mosfet.get_power()))

        if "H" in self.printer.heaters:
            answer += " " + format_temperature("H", "T1")

        if len(self.printer.coolers) > 0:
            cold_end = self.printer.coolers[0].get_temperature()
            answer += " C2:{0:.0f}".format(cold_end)
   
        g.set_answer(answer)

    def get_description(self):
        return "Get extruder temperature"

    def is_buffered(self):
        return False
