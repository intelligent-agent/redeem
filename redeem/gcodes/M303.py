"""
GCode M303
Run PID tuning 

Author: Elias Bakken
email: elias.bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/

PID Tuning refers to a control algorithm used in some repraps to 
tune heating behavior for hot ends and heated beds. 
This command generates Proportional (Kp), 
Integral (Ki), and Derivative (Kd) values for the hotend or bed (E-1). 
Send the appropriate code and wait for the output to update the firmware. 

"""
from __future__ import absolute_import

import json
import logging
import os
from .GCodeCommand import GCodeCommand
from redeem.Autotune import Autotune
from redeem.Alarm import Alarm


class M303(GCodeCommand):

    def execute(self, g):
        heater_nr = g.get_int_by_letter("H", 0)
        heater_name = ["HBP", "E", "H", "A", "B", "C"][heater_nr+1] # Map to name
        if not heater_name in self.printer.heaters:
            logging.warning("M303: Heater does not exist")
            return
        heater = self.printer.heaters[heater_name]
        temp     = g.get_float_by_letter("S", 200.0)        
        cycles   = max(3, g.get_int_by_letter("N", 4))       
        pre_cal  = bool(g.get_int_by_letter("P", 0))
        tuning_algo_nr = g.get_int_by_letter("L", 0)
        write_to_cfg = g.get_int_by_letter("W", 0)
        if tuning_algo_nr not in [0, 1]:
            logging.warning("Unknown tuning algorithm '{}'. Use one of 0, 1. Choosing 0.".format(tuning_algo_nr))
            tuning_algo_nr = 0
        tuning_algo = ["TL","ZN"][tuning_algo_nr]

        tuner = Autotune(heater, temp, cycles, g, self.printer, pre_cal, tuning_algo)
        if tuner.run():
            logging.info("Max temp: {}, Min temp: {}, Ku: {}, Pu: {}".format(tuner.max_temp, tuner.min_temp, tuner.Ku, tuner.Pu))
            logging.info("Kp: {}, Ti: {}, Td: {}".format(tuner.Kp, tuner.Ti, tuner.Td))
            self.printer.send_message(g.prot,"Max temp: {}, Min temp: {}, Ku: {}, Pu: {}".format(tuner.max_temp, tuner.min_temp, tuner.Ku, tuner.Pu))
            self.printer.send_message(g.prot, "Kp: {}, Ti: {}, Td: {}".format(tuner.Kp, tuner.Ti, tuner.Td))
            if not write_to_cfg:
                cfg = "Update settings by G-code: \n"
                cfg += "M130 P{} S{:.4f}\n".format(heater_nr, tuner.Kp)
                cfg += "M131 P{} S{:.4f}\n".format(heater_nr, tuner.Ti)
                cfg += "M132 P{} S{:.4f}\n".format(heater_nr, tuner.Td)
                cfg += "Save settings in local.cfg: \n"
                cfg += "[Temperature Control]\n[[{}]]\n".format(heater.input.name)
                cfg += "pid_Kp = {:.4f}\n".format(tuner.Kp)
                cfg += "pid_Ti = {:.4f}\n".format(tuner.Ti)
                cfg += "pid_Td = {:.4f}".format(tuner.Td)
                self.printer.send_message(g.prot, cfg)
            else:
                # Save the config file. Tuning parameters written to config in AutoTune.py
                self.printer.config.save(os.path.join(self.printer.config_location,'local.cfg'))
                self.printer.send_message(g.prot,"PID settings for {} ({}) saved in local.cfg".format(heater.name, heater.input.name))
    
            tune_data = {
                "tune_data": tuner.plot_temps,
                "tune_gcode": g.message,
                "replicape_key": self.printer.replicape_key}
    
            Alarm.action_command("pid_tune_data", json.dumps(tune_data))

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
            "\nInputs:\n"
            "H<0 or 1> overrides the extruder. Use H-1 for heated bed. \n"
            "Default is the 'E' extruder with index 0. \n"
            "S overrides the temperature to calibrate for. Default is 200. \n"
            "N overrides the number of cycles to run, default is 4 \n"
            "P (0,1) Enable pre-calibration. Useful for systems with very high power\n"
            "L Tuning algorithm. 0 = Tyreus-Luyben, 1 = Zieger-Nichols classic"
            "W Write to local.cfg. 0 = No, 1 = Yes")




