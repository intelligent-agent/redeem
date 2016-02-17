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
            answer.append(sensor.get_status())
            g.set_answer("".join(answer))

    def get_description(self):
        return "Get a status report from each filament sensor connected"

    def is_buffered(self):
        return False

