"""
GCode M117
Display a message. As a first implementation, just send to Toggle.

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: GNU GPL v3: http://www.gnu.org/copyleft/gpl.html
"""

from GCodeCommand import GCodeCommand

try:
    from Alarm import Alarm
except ImportError:
    from redeem.Alarm import Alarm

class M117(GCodeCommand):
    def execute(self, g):
        # This G-code can be used directly
        text = g.message.strip("M117 ")
        Alarm.action_command("display_message", text)
        #self.printer.comms["octoprint"].send_message(text)

    def get_description(self):
        return "Send a message to a connected display"

    def get_long_description(self):
        return ("Use 'M117 message' to send a message to a connected display. "
                "Typically this will be a Manga Screen or similar.")
