"""
Author: Andrew Mirsky
email: andrew@mirskytech.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/

M2x commands:

- M20: List SD card
- M21: Initialize SD card
- M22: Release SD card
- M23: Select SD file
- M24: Start/resume SD print
- M25: Pause SD print
- M26: Set SD position
- M27: Report SD print status

mount uses auto. if this doen't work, use parted library to determine format type
for more info, see https://github.com/vsinitsyn/fdisk.py/blob/master/fdisk.py

auto - this is a special one. It will try to guess the fs type when you use this.
ext4 - this is probably the most common Linux fs type of the last few years
ext3 - this is the most common Linux fs type from a couple years back
ntfs - this is the most common Windows fs type or larger external hard drives
vfat - this is the most common fs type used for smaller external hard drives
exfat - is also a file system option commonly found on USB flash drives and other external drives
"""

import os
from abc import abstractmethod, ABCMeta

import sh
import logging
from threading import Lock
from thread import start_new_thread

from GCodeCommand import GCodeCommand
from redeem.Gcode import Gcode

# multi thread management
# TODO : encapsulate this into an attribute of the printer. `SDCardManager`
current_file = None
current_line_count = None
current_file_count = None
current_lock = Lock()

# device_location = '/dev/mmcblk1p1'
USB_DEVICE_LOCATION = '/dev/sda1'
USB_MOUNT_LOCATION = '/media/usbmem'

SD_DEVICE_1_LOCATION = '/dev/mmcblk1p1'
SD_DEVICE_2_LOCATION = '/dev/mmcblk0p1'
SD_MOUNT_LOCATION = '/media/sdcard'

LCL_MOUNT_LOCATION = '/usr/share/models'

MOUNT_LOCATIONS = {
    '/usb': USB_MOUNT_LOCATION,
    '/sd': SD_MOUNT_LOCATION,
    '/lcl': LCL_MOUNT_LOCATION
}

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
    """utility function to check to make sure one of the correct devices is being requested"""
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
    """base class for all commands that work with external memory"""
    __metaclass__ = ABCMeta

    def is_buffered(self):
        return False


class M20(M2X):
    """list all files on an external memory device"""


    def execute(self, g):
        device_id = check_device_id(self.printer, g)
        if not device_id:
            return

        list_location = MOUNT_LOCATIONS[device_id]

        # check if the location exists (even if it isn't mounted, usb and sd should at least have the directory)
        if not os.path.exists(list_location):
            self.printer.send_message(g.prot, "external memory '{}' is not initialized".format(device_id))
            return

        # additional check to make sure usb and sd devices have been mounted
        if device_id in ['/usb', '/sd'] and not os.path.ismount(list_location):
            self.printer.send_message(g.prot, "external memory '{}' is not initialized".format(device_id))
            return

        # list all files on the device
        self.printer.send_message(g.prot, "files on external memory '{}'".format(list_location))
        for root, directories, filenames in os.walk(list_location):
            for filename in filenames:
                self.printer.send_message(g.prot, " - {}/{}".format(list_location, filename))

    def get_description(self):
        return """List all files on an external memory location"""

    def get_formatted_description(self):
            return """For an already attached external memory location, list all the files available. The
supported devices are:

{}

Use ``M21`` to attach a device.

::

    > M20 /usb
    - /usb/myfile.gcode
    - /usb/mydirectory/myotherfile.gcode
    - /usb/yetanotherfile.gcode

    > M20 /lcl
    - /lcl/example.gcode

"""


class M21(M2X):
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

        self.printer.send_message(g.prot, "external memory location now available: '{}'".format(mount_location))

    def get_description(self):
        return """Initialize external memory location"""

    def get_formatted_description(self):
        return """
        Attach external memory device, choose from:
{}

::

    > M20 /usb
    > M20 /sd

Use ``M22`` to unattach a device before removing. 

.. note:: local storage is always mounted, used with M21 will be a no-op
""".format(DEVICE_TABLE)


class M22(M2X):
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

.. note:: local storage is always mounted, used with M22 will be a no-op 
""".format(DEVICE_TABLE)


class M23(M2X):

    def execute(self, g):

        # TODO : what happens when this is called while a file is already being printed? different if machine is halted?
        logging.info("M23: starting gcode file processing")

        text = g.get_message()[len("M23"):]

        if not text.strip():
            self.printer.send_message(g.prot, "missing filename")
            return

        fn = text.strip()

        if fn.startswith('/usb/'):
            fn = fn.replace('/usb/', USB_MOUNT_LOCATION)

        if fn.startswith('/sd/'):
            fn = fn.replace('/sd/', SD_MOUNT_LOCATION)

        if fn.startswith('/lcl/'):
            fn = fn.replace('/lcl/', LCL_MOUNT_LOCATION)

        if not os.path.exists(fn):
            self.printer.send_message(g.prot, "could not find file at '{}'".format(text.strip()))
            return

        current_lock.acquire()
        current_file = fn
        current_lock.release()

    def get_description(self):
        return """"Select a file from external location"""

    def get_formatted_description(self):
        return """Choose a gcode file for printing from external location:
{}

::

    > M23 /usb/myfile.gcode
    > M23 /sd/myfolder/myotherfile.gcode
    > M23 /lcl/anotherfile.gcode
""".format(DEVICE_TABLE)


class M24(GCodeCommand):

    def process_gcode(self, fn):

        with open(fn, 'r') as gcode_file:
            logging.info("M23: file open")

            current_lock.acquire()
            current_file = gcode_file
            current_line_count = 0
            current_file_count = len(gcode_file)
            current_lock.release()

            for line in gcode_file:
                line = line.strip()

                current_lock.acquire()
                current_line_count += 1
                current_lock.release()

                if not line or line.startswith(';'):
                    continue
                file_g = Gcode({"message": line, "parent": g})
                self.printer.processor.execute(file_g)

            current_lock.acquire()
            current_file = None
            current_lint_count = None
            current_file_count = None
            current_lock.release()

            logging.info("M23: file complete")

    def execute(self, g):

        current_lock.acquire()
        fn = current_file
        current_lock.release()

        if fn:
            start_new_thread(self.process_gcode, (fn,))

        self.printer.path_planner.resume()

    def get_description(self):
        return "Resume the print where it was paused by the M25 command."

    def is_buffered(self):
        return False


class M25(GCodeCommand):

    def execute(self, g):
        self.printer.path_planner.suspend()

    def get_description(self):
        return "Pause the current print."

    def is_buffered(self):
        return False


class M27(M2X):

    # FIXME : if halted, current_line_count will only reflect the lines loaded into path planner, not actually executed
    # FIXME : adjust current_line_count by the number of commands in the path planner buffer

    def execute(self, g):
        message = " file '{}' printing: {} of {} lines"

        current_lock.acquire()
        message = message.format(current_file, current_line_count, current_file_count)
        current_lock.release()

        self.printer.send_message(g.prot, message)

        return

    def get_description(self):
        return """Report external file print status"""

    def get_formatted_description(self):
        return """Display current file being printed, the number of lines processed and the total number of lines
::
    > M27
    file '/usb/myfolder/myfile.gcode' printing: 10 of 211 lines
"""



