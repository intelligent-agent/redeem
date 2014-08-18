"""
GCode M117
Display a message. As a first imlementation, just send to Toggle.

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: GNU GPL v3: http://www.gnu.org/copyleft/gpl.html
"""

from GCodeCommand import GCodeCommand


class M117(GCodeCommand):
    def execute(self, g):
        # This G-code can be used directly
        text = g.message.strip("M117 ")
        self.printer.comms["toggle"].send_message(text)

    def get_description(self):
        return "Send a message to a connected display"
