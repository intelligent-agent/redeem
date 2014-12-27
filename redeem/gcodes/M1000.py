"""
GCode M1000
List all implemented G-codes (help)

Author: Elias Bakken
email: elias.bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand


class M1000(GCodeCommand):

    def execute(self, g):
        gcodes = self.printer.processor.get_supported_commands_and_description()
        self.printer.send_message(g.prot, "Implemented Gcodes:")
        for gcode, desc in sorted(gcodes.items()):
            self.printer.send_message(g.prot, gcode+": "+desc)

    def get_description(self):
        return "List all gcodes"
