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
- M28: TODO
- M29: TODO

mount uses auto. if this doen't work, use parted library to determine format type
for more info, see https://github.com/vsinitsyn/fdisk.py/blob/master/fdisk.py

auto - this is a special one. It will try to guess the fs type when you use this.
ext4 - this is probably the most common Linux fs type of the last few years
ext3 - this is the most common Linux fs type from a couple years back
ntfs - this is the most common Windows fs type or larger external hard drives
vfat - this is the most common fs type used for smaller external hard drives
exfat - is also a file system option commonly found on USB flash drives and other external drives
"""
from __future__ import absolute_import

import os
from abc import abstractmethod, ABCMeta

import sh
import logging
from threading import Lock
from thread import start_new_thread

from time import sleep

from .GCodeCommand import GCodeCommand
from redeem.Gcode import Gcode

import cProfile, pstats, StringIO

# device_location = '/dev/mmcblk1p1'
USB_DEVICE_LOCATION = '/dev/sda1'
USB_MOUNT_LOCATION = '/media/usbmem'

SD_DEVICE_1_LOCATION = '/dev/mmcblk1p1'
SD_DEVICE_2_LOCATION = '/dev/mmcblk0p1'
SD_MOUNT_LOCATION = '/media/sdcard'

LCL_MOUNT_LOCATION = '/usr/share/models'

MOUNT_LOCATIONS = {'/usb': USB_MOUNT_LOCATION, '/sd': SD_MOUNT_LOCATION, '/lcl': LCL_MOUNT_LOCATION}

DEVICE_TABLE = """
==== ===========================
id   device
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
    # printer.send_message(g.prot, "device id not specified")
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
      device_id = "/lcl"

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
    self.printer.send_message(g.prot, "Begin file list:")
    for root, directories, filenames in os.walk(list_location):
      for filename in filenames:
        if not filename.startswith('.'):
          file_byte_count = os.stat(root + os.sep + filename).st_size
          self.printer.send_message(g.prot, "{}/{} {}".format(device_id, filename, file_byte_count))
    self.printer.send_message(g.prot, "End file list")

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

""".format(DEVICE_TABLE)


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
      # default to trick OctoPrint into seeing all files listed as available for SD printing
      self.printer.send_message(g.prot, "SD card ok")
      return
    device_location, mount_location = None, None
    if device_id == '/usb':
      device_location, mount_location = self._mount(g, USB_DEVICE_LOCATION, USB_MOUNT_LOCATION)
    if device_id == '/sd':
      device_location, mount_location = self._mount(g, SD_DEVICE_1_LOCATION, SD_MOUNT_LOCATION)
      if not mount_location:
        device_location, mount_location = self._mount(g, SD_DEVICE_2_LOCATION, SD_MOUNT_LOCATION)
    if device_id == '/lcl':
      device_location, mount_location = None, LCL_MOUNT_LOCATION
    if not mount_location:
      self.printer.send_message(g.prot, "external memory location could not be attached")

  def get_description(self):
    return """Initialize external memory location"""

  def get_formatted_description(self):
    return """Attach external memory device, choose from:

{}

::

    > M20 /usb
    > M20 /sd

Use ``M22`` to unattach a device before removing.

.. note:: local storage is always mounted; used with M21 will be a no-op
""".format(DEVICE_TABLE)


class M22(M2X):
  def execute(self, g):
    device_id = check_device_id(self.printer, g)
    if not device_id:
      return

    if device_id == '/usb':
      sh.umount(USB_MOUNT_LOCATION)
      self.printer.send_message(g.prot, "external memory location closed '{}'".format(device_id))

    if device_id == '/sd':
      sh.umount(SD_DEVICE_1_LOCATION)
      sh.umount(SD_DEVICE_2_LOCATION)

  def get_description(self):
    return """Release external memory location"""

  def get_formatted_description(self):
    return """Disconnect external memory device, choose from:
{}

::

    > M21 /usb
    > M21 /sd

.. note:: local storage is always mounted; used with M22 will be a no-op
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
    list_location = None

    if fn.startswith('/usb'):
      fn = fn.replace('/usb', USB_MOUNT_LOCATION)
      list_location = USB_MOUNT_LOCATION
    if fn.startswith('/sd'):
      fn = fn.replace('/sd', SD_MOUNT_LOCATION)
      list_location = SD_MOUNT_LOCATION
    if fn.startswith('/lcl'):
      fn = fn.replace('/lcl', LCL_MOUNT_LOCATION)
      list_location = LCL_MOUNT_LOCATION

    filemap = dict()
    for root, directories, filenames in os.walk(list_location):
      for file in filenames:
        filepath = root + os.sep + file
        filemap[filepath.lower()] = filepath

    if fn in filemap:
      fn = filemap[fn]

    if not os.path.exists(fn):
      self.printer.send_message(g.prot, "could not find file at '{}'".format(fn.strip()))
      return

    self.printer.sd_card_manager.load_file(fn)
    nl, nb = self.printer.sd_card_manager.get_file_size()
    self.printer.send_message(g.prot, "File opened:{} Size:{}".format(fn, nb))
    self.printer.send_message(g.prot, "File selected")
    logging.info("M23: finished gcode file processing")

  def get_description(self):
    return """Choose a file from external location"""

  def get_formatted_description(self):
    return """Choose a gcode file for printing from external location:
{}

::

    > M23 /usb/myfile.gcode
    > M23 /sd/myfolder/myotherfile.gcode
    > M23 /lcl/anotherfile.gcode
""".format(DEVICE_TABLE)


class M24(GCodeCommand):
  def process_gcode(self, g):
    profile = cProfile.Profile()
    self.printer.sd_card_manager.set_status(True)
    profile.enable()
    for line in self.printer.sd_card_manager:
      line = line.strip()
      if not line or line.startswith(';'):
        continue
      file_g = Gcode({"message": line})
      self.printer.processor.enqueue(file_g)
    if self.printer.sd_card_manager.get_status():
      logging.info("M24: Print from file complete")
    self.printer.sd_card_manager.set_status(False)

    self.printer.send_message(g.prot, "Done printing file")
    profile.disable()
    s = StringIO.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(profile, stream=s).sort_stats(sortby)
    ps.print_stats()
    logging.debug(s.getvalue())
    self.printer.sd_card_manager.reset()

  def execute(self, g):
    fn = self.printer.sd_card_manager.get_file_name()
    active = self.printer.sd_card_manager.get_status()
    if not active:
      logging.info("M24: Printing file '{}'".format(fn))
      start_new_thread(self.process_gcode, (g, ))
      # allow some time for the new thread to start before we proceed
      counter = 0
      while (not active) and (counter < 10):
        sleep(0.1)
        counter += 1
    self.printer.path_planner.resume()
    self.printer.send_message(g.prot, "ok : M24 in progress")

  def get_description(self):
    return "Start/unpause a print"

  def get_formatted_description(self):
    return """Start printing from an externally selected file using the ``M23`` command.

If the current print (from any source) was paused by ``M25``, this will resume the print."""

  def is_buffered(self):
    return False


class M25(GCodeCommand):
  def execute(self, g):
    self.printer.sd_card_manager.set_status(False)

  def get_description(self):
    return "Pause the current SD print."

  def is_buffered(self):
    return False


class M26(M2X):
  def execute(self, g):
    S = g.get_int_by_letter("S", 0)
    L = g.get_int_by_letter("L", 0)
    line_position, byte_position = self.printer.sd_card_manager.set_position(
        byte_position=S, line_position=L)
    size_lines, size_bytes = self.printer.sd_card_manager.get_file_size()
    message = "SD at line {}/{}, byte {}/{}".format(line_position, size_lines, byte_position,
                                                    size_bytes)
    self.printer.send_message(g.prot, message)

  def get_description(self):
    return "Set SD card print position"

  def get_formatted_description(self):
    return """Set SD card print position.

    S = position in bytes
    L = line number

::

    > M26 S0
    or
    > M26 L10

"""


class M27(M2X):
  def execute(self, g):
    line_position, byte_position = self.printer.sd_card_manager.get_position()
    size_lines, size_bytes = self.printer.sd_card_manager.get_file_size()
    file_name = self.printer.sd_card_manager.get_file_name()
    # message to inform that we have completed the print
    if file_name is None:
      message = "Not SD printing."
    else:
      message = "SD printing byte {}/{}".format(byte_position, size_bytes)
    self.printer.send_message(g.prot, message)
    logging.debug(message)

  def get_description(self):
    return """Report external file print status"""

  def get_formatted_description(self):
    return """If printing from an externally selected file (from ``M23``), display of how many bytes
from the active file have been processed.

::

    > M27
    SD printing byte 10/1231

"""


#class M28(M2X):
#
#    def execute(self, g):
#        self.printer.send_message(g.prot, "M28 not implemented")
#        self.printer.send_message(g.prot, "use M20 instead to list local files as sd files")
#        self.printer.send_message(g.prot, "if you used the 'Upload to SD' button in OctoPrint you will now need to disconnect/reconnect Redeem because Octoprint is being dumb")
#
#        # Octoprint expects 'Writing to file' but we don't want that
#
#    def get_description(self):
#        return "Placeholder for write to SD card, use M20 instead"
#
#    def get_formatted_description(self):
#        return """Placeholder for write to SD card, use M20 instead"""
#
#class M29(M2X):
#
#    def execute(self, g):
#        self.printer.send_message(g.prot, "Done saving file")
#
#    def get_description(self):
#        return "Placeholder for end write to SD card"
#
#    def get_formatted_description(self):
#        return """Placeholder for end write to SD card"""
