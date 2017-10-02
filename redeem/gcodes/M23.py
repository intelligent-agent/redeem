"""
GCode M23
Select SD file

Author: Andrew Mirsky
email: andrew@mirskytech.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand

import ctypes
import os

import parted

from redeem.Gcode import Gcode


class M23(GCodeCommand):

    @staticmethod
    def mount(source, target, fs, options=''):
        ret = ctypes.CDLL('libc.so.6', use_errno=True).mount(source, target, fs, 0, options)
        if ret < 0:
            errno = ctypes.get_errno()
            raise RuntimeError("Error mounting {} ({}) on {} with options '{}': {}".
                               format(source, fs, target, options, os.strerror(errno)))

    def execute(self, g):

        device_location = '/dev/mmcblk0p1'
        mount_location = '/media/sdcard'

        if not os.path.ismount(mount_location):

            fstype = 'exfat'

            # check to see if there is a device available for reading
            device = parted(device_location)
            disk = parted.newDisk(device)

            if disk.type == 'msdos':
                fstype = 'msdos'
            elif disk.type == 'vfat':
                fstype = 'vfat'

            self.mount(device_location, mount_location, fstype, 'r')

        if not os.path.ismount(mount_location):
            self.printer.send_message("could not mount device '{}'".format(device_location))
            return

        text = g.get_message()[len("M23"):]
        fn = os.path.join(mount_location, text.strip())

        if not os.path.exists(fn):
            self.printer.send_message("could not find file at '{}'".format(fn))
            return

        with open(fn, 'r') as gcode_file:

            for line in gcode_file:

                line = line.strip()
                if not line or line.startswith(';'):
                    continue

                file_g = Gcode({"message": line, "parent": g})
                self.printer.processor.execute(file_g)

    def get_description(self):
        return """"Select a file from the SD Card"""

    def get_formatted_description(self):
        return """
Load *and begin printing* a gcode file from an sdcard.
        """

    def is_buffered(self):
        return False
