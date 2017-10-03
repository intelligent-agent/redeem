"""
GCode M23
Select SD file

Author: Andrew Mirsky
email: andrew@mirskytech.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand

import os
import logging

from sh import mount, ErrorReturnCode_32
from thread import start_new_thread

from redeem.Gcode import Gcode

"""
auto - this is a special one. It will try to guess the fs type when you use this.
ext4 - this is probably the most common Linux fs type of the last few years
ext3 - this is the most common Linux fs type from a couple years back
ntfs - this is the most common Windows fs type or larger external hard drives
vfat - this is the most common fs type used for smaller external hard drives
exfat - is also a file system option commonly found on USB flash drives and other external drives
"""

class M23(GCodeCommand):

    @staticmethod
    def mount(g, source, target, fstype=None, options=''):

        try:
            ret = mount(source, target)
        except ErrorReturnCode_32:
            g.printer.send_message(g.prot, "could not mount: {} to {} - {}".format(source, target, ret))

    def process_gcode(self, g, fn):

        logging.info("M23: starting gcode file processing")

        if not os.path.exists(fn):
            self.printer.send_message(g.prot, "could not find file at '{}'".format(fn))
            return

        with open(fn, 'r') as gcode_file:
            logging.info("M23: file open")

            for line in gcode_file:
                line = line.strip()
                if not line or line.startswith(';'):
                    continue
                file_g = Gcode({"message": line, "parent": g})
                self.printer.processor.execute(file_g)

        logging.info("M23: file complete")

    def execute(self, g):

        # device_location = '/dev/mmcblk1p1'
        device_location = '/dev/sda1'
        mount_location = '/media/usbmem'

        if not os.path.isdir(mount_location):
            os.mkdir(mount_location)

        if not os.path.ismount(mount_location):

            self.mount(g, device_location, mount_location)

        if not os.path.ismount(mount_location):
            self.printer.send_message(g.prot, "could not mount device '{}'".format(device_location))
            return

        text = g.get_message()[len("M23"):]

        if not text.strip():
            self.printer.send_message(g.prot, "missing filename")
            return

        fn = os.path.join(mount_location, text.strip())

        start_new_thread(self.process_gcode, (g, fn))

    def get_description(self):
        return """"Select a file from the SD Card"""

    def get_formatted_description(self):
        return """Load *and begin printing* a gcode file from a usb memory stick.
::

    > M23 circle.gcode
    > M23 afoldername/circle.gcode
"""

    def is_buffered(self):
        return False
