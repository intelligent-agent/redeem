"""
GCode M117
Display a message. As a first implementation, just send to Toggle.

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: GNU GPL v3: http://www.gnu.org/copyleft/gpl.html
"""
from __future__ import absolute_import

from .GCodeCommand import GCodeCommand
from ..Alarm import Alarm


class M117(GCodeCommand):
    def execute(self, g):
        text = g.get_message()[len("M117"):]
        if text[0] == ' ':
            text = text[1:]
        Alarm.action_command("display_message", text.rstrip())

    def get_description(self):
        return "Send a message to a connected display"

    def get_long_description(self):
        return ("Use 'M117 message' to send a message to a connected display. "
                "Typically this will be a Manga Screen or similar.")
