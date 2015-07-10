"""
GCode M303
Run PID tuning 

Author: Elias Bakken
email: elias.bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/

PID Tuning refers to a control algorithm used in some repraps to tune heating behavior for hot ends and heated beds. This command generates Proportional (Kp), Integral (Ki), and Derivative (Kd) values for the hotend or bed (E-1). Send the appropriate code and wait for the output to update the firmware. 

"""

from GCodeCommand import GCodeCommand
try:
    from Autotune import Autotune
except ImportError:
    from redeem.Autotune import Autotune
import logging


class M303(GCodeCommand):

    def execute(self, g):
        if g.has_letter("E"):
            if int(g.get_value_by_letter("E")) == 0:
                heater = self.printer.heaters["E"]
            elif int(g.get_value_by_letter("E")) == 1:
                heater = self.printer.heaters["H"]
            elif int(g.get_value_by_letter("E")) == -1:
                heater = self.printer.heaters["HBP"]
        else:
            heater = self.printer.heaters["E"]

        if g.has_letter("S"):
            temp = float(g.get_value_by_letter("S"))
        else:
            temp = 100.0

        if g.has_letter("C"):
            cycles = int(g.get_value_by_letter("C"))
        else:
            cycles = 3
        
        tuner = Autotune(heater, temp, cycles)
        tuner.run()
        logging.info("Max temp: {}, Min temp: {}, Ku: {}, Pu: {}".format(tuner.max_temp, tuner.min_temp, tuner.Ku, tuner.Pu))
        logging.info("P: {}, I: {}, D: {}".format(heater.P, heater.I, heater.D))
        self.printer.send_message(g.prot,"Max temp: {}, Min temp: {}, Ku: {}, Pu: {}".format(tuner.max_temp, tuner.min_temp, tuner.Ku, tuner.Pu))
        self.printer.send_message(g.prot, "P: {}, I: {}, D: {}".format(heater.P, heater.I, heater.D))

    def is_buffered(self):
        return True

    def get_description(self):
        return "Run PID tuning"

    def get_long_description(self):
        return ("PID Tuning refers to a control algorithm "
            "used in some repraps to tune heating behavior "
            "for hot ends and heated beds. This command "
            "generates Proportional (Kp), Integral (Ki), "
            "and Derivative (Kd) values for the hotend or "
            "bed (E-1). Send the appropriate code and wait "
            "for the output to update the firmware. ")
