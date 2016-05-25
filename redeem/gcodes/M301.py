"""
GCode M301
Adjust PID settings

Author: Elias Bakken
email: elias(at)iagent(dot)no
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand


class M301(GCodeCommand):

    def execute(self, g):
        Kp = g.get_float_by_letter("P", 0.0)
        Ti = g.get_float_by_letter("I", 0.0)
        Td = g.get_float_by_letter("D", 0.0)
        extr = g.get_int_by_letter("E", 0)
        heater =  self.printer.heaters[["HBP", "E", "H", "A", "B", "C"][extr+1]]
        heater.Kp = Kp
        heater.Ti = Ti
        heater.Td = Td
        
    def get_description(self):
        return "Set P, I and D values, Format (M301 E0 P0.1 I100.0 D5.0)"

    def get_long_description(self):
        return ("Set P, I and D values, Format (M301 E0 P0.1 I100.0 D5.0)"
                "P = Kp, default = 0.0"
                "I = Ti, default = 0.0"
                "D = Td, default = 0.0"
                "E = Extruder, -1=Bed, 0=E, 1=H, 2=A, 3=B, 4=C, default = 0")
