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
    from Autotune_1 import Autotune_1
    from Autotune_2 import Autotune_2
except ImportError:
    from redeem.Autotune_1 import Autotune_1
    from redeem.Autotune_2 import Autotune_2

import logging


class M303(GCodeCommand):

    def execute(self, g):
        heater_nr = g.get_int_by_letter("E", 0)
        heater_name = ["HBP", "E", "H", "A", "B", "C"][heater_nr+1] # Map to name
        if not heater_name in self.printer.heaters:
            logging.warning("M303: Heater does not exist")
        heater = self.printer.heaters["E"]
        temp     = g.get_float_by_letter("S", 200.0)
        cycles   = g.get_int_by_letter("C", 4)            
        tuner_nr = g.get_int_by_letter("N", 1)

        if tuner_nr == 1:
            tuner = Autotune_1(heater, temp, cycles, g, self.printer)
        elif tuner_nr == 2:
            tuner = Autotune_2(heater, temp, cycles, g, self.printer)
        else:
            logging.warning("M303: Tuner does not exist")
            return
        tuner.run()
        logging.info("Max temp: {}, Min temp: {}, Ku: {}, Pu: {}".format(tuner.max_temp, tuner.min_temp, tuner.Ku, tuner.Pu))
        logging.info("Kp: {}, Ti: {}, Td: {}".format(heater.Kp, heater.Ti, heater.Td))
        self.printer.send_message(g.prot,"Max temp: {}, Min temp: {}, Ku: {}, Pu: {}".format(tuner.max_temp, tuner.min_temp, tuner.Ku, tuner.Pu))
        self.printer.send_message(g.prot, "P: {}, I: {}, D: {}".format(heater.Kp, heater.Ti, heater.Td))

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
            "for the output to update the firmware. "
            "E<0 or 1> overrides the extruder. Use E-1 for heated bed. \n"
            "Default is the 'E' extruder with index 0. \n"
            "S overrides the temperature to calibrate for. Default is 200. \n"
            "C overrides the number of cycles to run, default is 3 \n"
            "N overrides the tuner number. 1 is the standard tuner, 2 is more advanced.")



