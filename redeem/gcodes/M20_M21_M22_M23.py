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

import sh

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

current_file = None

# device_location = '/dev/mmcblk1p1'
USB_DEVICE_LOCATION = '/dev/sda1'
USB_MOUNT_LOCATION = '/media/usbmem'

SD_DEVICE_1_LOCATION = '/dev/mmcblk1p1'
SD_DEVICE_2_LOCATION = '/dev/mmcblk0p1'
SD_MOUNT_LOCATION = '/media/sdcard'

LCL_MOUNT_LOCATION = '/usr/share/models'

DEVICE_TABLE = """
==== ===========================
id  device        
==== ===========================
/usb usb memory attached to host
/sd  microsd card
/lcl local storage (octoprint)
==== ===========================
"""


def check_device_id(printer, g):
    text = g.get_message()[len("M2X"):]

    if not text.strip():
        printer.send_message(g.prot, "device id not specified")
        return None

    device_id = text.strip()

    if device_id not in ['/usb', '/sd', '/lcl']:
        printer.send_message(g.prot, "device id not recognized '{}'".format(device_id))
        printer.send_message(g.prot, "must be one of /usb, /sd or /lcl")
        return None

    return device_id


class M2X(GCodeCommand):

    def is_buffered(self):
        return False


class M20(M2X):

    def _mount(self, g, source, target, fstype=None, options=''):

        if not os.path.isdir(target):
            os.mkdir(target)
        if os.path.ismount(target):
            return source, target
        try:
            sh.mount(source, target)
            return source, target
        except sh.ErrorReturnCode_32:
            self.printer.send_message(g.prot, "could not mount: {} to {}".format(source, target))
        return source, None

    def execute(self, g):

        device_id = check_device_id(self.printer, g)
        if not device_id:
            return

        device_location, mount_location = None, None

        if device_id == 'usb':
            device_location, mount_location = self._mount(g, USB_DEVICE_LOCATION, USB_MOUNT_LOCATION)

        if device_id == 'sd':
            device_location, mount_location = self._mount(g, SD_DEVICE_1_LOCATION, SD_MOUNT_LOCATION)
            if not mount_location:
                device_location, mount_location = self._mount(g, SD_DEVICE_2_LOCATION, SD_MOUNT_LOCATION)

        if device_id == 'lcl':
            device_location, mount_location = None, LCL_MOUNT_LOCATION

    def get_description(self):
        return """Initialize external memory location"""

    def get_formatted_description(self):
        return """
        Attach external memory device, choose from:
{}

::

    > M20 usb
    > M20 sd
    
.. note:: local storage is always mounted, used with M20 will be a no-op
""".format(DEVICE_TABLE)


class M21(M2X):

    def execute(self, gcode):
        device_id = check_device_id(self.printer, g)
        if not device_id:
            return

        if device_id == 'usb':
            sh.umount(USB_MOUNT_LOCATION)

        if device_id == 'sd':
            sh.umount(SD_DEVICE_1_LOCATION)
            sh.umount(SD_DEVICE_2_LOCATION)

    def get_description(self):
        return """"Release external memory location"""

    def get_formatted_description(self):
        return """
        Disconnect external memory device, choose from:
{}

::

    > M21 usb
    > M21 sd
    
.. note:: local storage is always mounted, used with M21 will be a no-op 
""".format(DEVICE_TABLE)


class M23(M2X):

    def process_gcode(self, fn):

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

        logging.info("M23: starting gcode file processing")

        text = g.get_message()[len("M23"):]

        if not text.strip():
            self.printer.send_message(g.prot, "missing filename")
            return

        fn = text.strip()

        if fn.startswith('/usb/'):
            fn = fn.replace('/usb', USB_MOUNT_LOCATION)

        if fn.startswith('/sd/'):
            fn = fn.replace('/sd', SD_MOUNT_LOCATION)

        if fn.startswith('/lcl/'):
            fn = fn.replace('/lcl/', LCL_MOUNT_LOCATION)

        if not os.path.exists(fn):
            self.printer.send_message(g.prot, "could not find file at '{}'".format(fn))
            return

        start_new_thread(self.process_gcode, (g, fn))

    def get_description(self):
        return """"Select a file from the SD Card"""

    def get_formatted_description(self):
        return """Load *and begin printing* a gcode file from external location, choose from:
{}
        
::

    > M23 /usb/myfile.gcode
    > M23 /sd/myfolder/myotherfile.gcode
    > M23 /lcl/anotherfile.gcode
""".format(DEVICE_TABLE)

