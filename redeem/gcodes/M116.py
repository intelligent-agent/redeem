"""
GCode M116
Wait for all temperature to be reached

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
try:
    from Gcode import Gcode
except ImportError:
    from redeem.Gcode import Gcode
import time
import logging


class M116(GCodeCommand):
    def execute(self, g):
        all_ok = [False, False, False]
        while True:
            all_ok[0] |= self.printer.heaters['E'].is_target_temperature_reached()
            all_ok[1] |= self.printer.heaters['H'].is_target_temperature_reached()
            all_ok[2] |= self.printer.heaters['HBP'].is_target_temperature_reached()
            m105 = Gcode({"message": "M105", "prot": g.prot})
            self.printer.processor.execute(m105)
            if not False in all_ok:
                logging.info("Heating done.")
                self.printer.send_message(g.prot, "Heating done.")
                self.printer.reply(m105)
                return
            else:
                answer = m105.get_answer()
                answer += " E: " + ("0" if self.printer.current_tool == "E" else "1")
                m105.set_answer(answer[2:])  # strip away the "ok"
                self.printer.reply(m105)
                time.sleep(1)

    def get_description(self):
        return "Wait for all temperature to be reached"

    def is_buffered(self):
        return True
