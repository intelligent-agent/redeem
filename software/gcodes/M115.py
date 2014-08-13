"""
GCode M115
Get Firmware Version and Capabilities

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand


class M115(GCodeCommand):
    def execute(self, g):
        #FIXME: Adjust the answer according to http://reprap.org/wiki/M115_Keywords
        g.set_answer(
            "ok PROTOCOL_VERSION:0.1 FIRMWARE_NAME:Redeem "
            "FIRMWARE_URL:http%3A//wiki.thing-printer.com/index.php?title="
            "Replicape MACHINE_TYPE:Mendel EXTRUDER_COUNT:2")

    def get_description(self):
        return "Get Firmware Version and Capabilities"
