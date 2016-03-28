"""
GCode M409
Get filament sensor status
Author: Elias Bakken
"""

from GCodeCommand import GCodeCommand
import logging


class M409(GCodeCommand):

    def execute(self, g):

        answer = ["ok "]
        for sensor in self.printer.filament_sensors:
            if g.has_letter("F"):
                answer.append(sensor.get_status())
                g.set_answer("".join(answer))
            # Enable action command
            elif g.has_letter("E"):
                if g.has_letter_value("E"):
                    sensor_number = g.get_int_by_letter("E", -1)
                    if sensor_number == sensor.ext_nr:
                        sensor.enable_sending_action_command()
                else:
                    sensor.enable_sending_action_command()
            # Disable action command
            elif g.has_letter("D"):
                if g.has_letter_value("D"):
                    sensor_number = g.get_int_by_letter("D", -1)
                    if sensor_number == sensor.ext_nr:
                        sensor.disable_sending_action_command()
                else:
                    sensor.disable_sending_action_command()

            else:
                answer.append(sensor.get_error())
                g.set_answer(" ".join(answer))
                

    def get_description(self):
        return "Get a status report from each filament sensor connected, or enable action command"


    def get_long_description(self):
        return ("Get a status report from each filament sensor connected"
                "If the token 'F' is present, get a human readable status. If "
                "no token is present, return a machine readable form, similar to "
                " the return from temperature sensors, M105. "
                "If token 'E' is present without token value, enable sending "
                "filament data for all sensors. If a value is present, enable sending "
                "filament data for this extruder number. "
                "Ex: M409 E0 - enables sending filament data for Extruder 0 (E), "
                "M409 E - Enable action command filament data for all filament sensors"
                "M409 D - Disable sending filament data for all filament sensors")

    def is_buffered(self):
        return False

