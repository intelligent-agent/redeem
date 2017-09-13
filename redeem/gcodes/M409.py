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
            if g.has_letter("H"):
                answer.append(sensor.get_status())
                g.set_answer("".join(answer))
            # Enable action command
            elif g.has_letter("S"):
                if g.has_letter_value("S"):
                    sensor_number = g.get_int_by_letter("S", -1)
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
                "If the token 'H' is present, get a human readable status. If "
                "no token is present, return a machine readable form, similar to "
                " the return from temperature sensors, M105.\n\n"
                "If token 'S' is present without token value, enable sending "
                "filament data for all sensors. If a value is present, enable sending "
                "filament data for this extruder number.\n\n"
                "Examples:\n\n"
                "  M409 S0 - enables sending filament data for Extruder 0 (E)\n "
                "  M409 S - Enable action command filament data for all filament sensors\n"
                "  M409 D - Disable sending filament data for all filament sensors")

    def is_buffered(self):
        return False

