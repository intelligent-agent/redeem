"""
GCode M116
Wait for all temperature to be reached

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

import time
import logging
from .GCodeCommand import GCodeCommand
from redeem.Gcode import Gcode



class M116(GCodeCommand):
    def execute(self, g):
        self.printer.running_M116 = True

        # heater_index:
        # -1 - HBP, 0 - E, 1 - H, 2 - A, 3 - B, 4 - C
        # No P or H Parameter means all temperatures must be reached

        has_parameter = g.has_letter("P") or g.has_letter("T")
        if has_parameter:
            if g.has_letter("P"):  # Set hotend temp based on the P-param
                heater_index = g.get_int_by_letter("P", 0)
            elif g.has_letter("T"):  # Set hotend temp based on the T-param
                heater_index = g.get_int_by_letter("T", 0)
            if heater_index > len(self.printer.heaters) - 1:
                logging.warning("M116: heater index out of bounds: {}".format(heater_index))
                return

        all_ok = [
            has_parameter and heater_index != 0,
            has_parameter and heater_index != 1,
            has_parameter and heater_index != -1
        ]
        if self.printer.config.reach_revision:
            all_ok.extend([
                has_parameter and heater_index != 2,
                has_parameter and heater_index != 3,
                has_parameter and heater_index != 4
            ])

        stable_time = 3.0
        while True:
            all_ok[0] |= self.printer.heaters['E'].is_temperature_stable()
            all_ok[1] |= self.printer.heaters['H'].is_temperature_stable()
            all_ok[2] |= self.printer.heaters['HBP'].is_temperature_stable()

            if self.printer.config.reach_revision:
                all_ok[3] |= self.printer.heaters['A'].is_temperature_stable()
                all_ok[4] |= self.printer.heaters['B'].is_temperature_stable()
                all_ok[5] |= self.printer.heaters['C'].is_temperature_stable()

            m105 = Gcode({"message": "M105", "parent": g})
            self.printer.processor.execute(m105)
            if False not in all_ok or not self.printer.running_M116:
                logging.info("Heating done.")
                self.printer.send_message(g.prot, "ok Heating done.")
                self.printer.running_M116 = False
                return
            else:
                answer = m105.get_answer()
                answer += " E: " + ("0" if self.printer.current_tool == "E" else "1")
                m105.set_answer(answer[2:])  # strip away the "ok"
                self.printer.reply(m105)
                time.sleep(1)

    def get_description(self):
        return "Wait for a specific temperature/all temperatures to be reached"

    def get_long_description(self):
        desc = ("Wait for a specific temperature/all temperatures to be reached"
                "If no parameter is added M116 will wait for all temperatures to be reached"
                "If P or T is set then M116 will wait for the specific Heater to reach temperature only"
                "Possible values are: \n"
                "-1 - Heated Bed \n"
                " 0 - Extruder E\n"
                " 1 - Extruder H")
        # unittests and docs may not have printer set when looking for docs
        if not self.printer or self.printer.config.reach_revision:
            desc += (" 2 - Extruder A\n"
                    " 3 - Extruder B\n"
                    " 4 - Extruder C")
        return desc

    def is_buffered(self):
        return True
