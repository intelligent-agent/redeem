"""
GCode M115
Get Firmware Version and Capabilities

Author: Richard Wackerbarth
email: rkw(at)dataplex(dot)net
Original Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

from .GCodeCommand import GCodeCommand
from redeem import __url__, __long_version__
import os


class M115(GCodeCommand):
  def execute(self, g):
    protocol_version = 0.1
    printer_key = self.printer.key
    firmware_name = "Redeem"
    firmware_version = __long_version__
    firmware_url = __url__
    machine_type = self.printer.config.get('System', 'machine_type')
    extruder_count = self.printer.NUM_EXTRUDERS
    kernel = os.uname()[2]
    # get distro will come from /etc/issue or /etc/kamikaze-release
    f = open('/etc/kamikaze-release', 'r')
    l = f.readline().split(" ")
    f.close()
    distro_name = l[0]
    distro_version = l[1]
    g.set_answer(
        "ok " \
        "PROTOCOL_VERSION:{} "\
        "FIRMWARE_NAME:{} "\
        "FIRMWARE_VERSION:{} "\
        "PRINTER_KEY:{} "\
        "FIRMWARE_URL:{} "\
        "MACHINE_TYPE:{} "\
        "KERNEL:{} "\
        "DISTRIBUTION_NAME:{} "\
        "DISTRIBUTION_VERSION:{} "\
        "EXTRUDER_COUNT:{}"\
        .format(
            protocol_version,
            firmware_name,
            firmware_version,
            printer_key,
            firmware_url,
            machine_type,
            kernel,
            distro_name,
            distro_version,
            extruder_count
        )
    )

  def get_description(self):
    return "Get Firmware Version and Capabilities"

  def get_long_description(self):
    return ("Get Firmware Version and Capabilities"
            "Will return the version of Redeem running, "
            "the machine type and the extruder count. ")
