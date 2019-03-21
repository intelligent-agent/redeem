#!/usr/bin/env python
"""
This is an implementation of the PWM DAC

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: GNU GPL v3: http://www.gnu.org/copyleft/gpl.html

 Redeem is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Redeem is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Redeem.  If not, see <http://www.gnu.org/licenses/>.
"""

from Adafruit_GPIO.I2C import Device as I2C

import time
import subprocess
import logging
import os
import glob


class PWM_Output(object):
  def set_value(self, value):
    raise NotImplementedError()


class PWM_PCA9685_Output(PWM_Output):
  def __init__(self, controller, channel):
    self.controller = controller
    self.channel = channel

  def set_value(self, value):
    self.controller.set_value(self.channel, value)


class PWM_PCA9685(object):

  frequency = 0
  i2c = None

  PCA9685_MODE1 = 0x0
  PCA9685_PRESCALE = 0xFE

  def __init__(self, i2c_address, i2c_bus):
    self.i2c = I2C(i2c_address, i2c_bus)
    self.i2c.write8(self.PCA9685_MODE1, 0x01)    # Reset
    self.i2c._logger.setLevel(logging.WARNING)

  def set_frequency(self, freq):
    """ Set the PWM frequency for all fans connected on this PWM-chip """
    prescaleval = 25000000
    prescaleval /= 4096
    prescaleval /= float(freq)
    prescaleval = int(prescaleval + 0.5)
    prescaleval -= 1

    oldmode = self.i2c.readU8(self.PCA9685_MODE1)
    newmode = (oldmode & 0x7F) | 0x10
    self.i2c.write8(self.PCA9685_MODE1, newmode)
    self.i2c.write8(self.PCA9685_PRESCALE, prescaleval)
    self.i2c.write8(self.PCA9685_MODE1, oldmode)
    time.sleep(0.05)
    self.i2c.write8(self.PCA9685_MODE1, oldmode | 0xA1)

    self.frequency = freq

  def set_value(self, channel, value):
    """ Set the amount of on-time from 0..1 """
    off = int(value * 4095)
    byte_list = [0x00, 0x00, off & 0xFF, off >> 8]
    self.i2c.writeList(0x06 + (4 * channel), byte_list)

  def get_output(self, channel):
    return PWM_PCA9685_Output(self, channel)


class PWM_AM335_Output(PWM_Output):
  def __init__(self, base_path):
    self.base_path = base_path
    self.enabled = True
    self.set_frequency(1000)    # TODO this should probably be a parameter
    self.set_enabled(False)

  def set_value(self, value):
    """ Set the amount of on-time from 0..1 """
    duty_cycle = int(self.period * float(value))
    path = self.base_path + "/duty_cycle"
    with open(path, "w") as f:
      f.write(str(duty_cycle))
    # Call enable/disable here since the timer pins
    self.set_enabled((value > 0))

  def set_enabled(self, is_enabled=True):
    if self.enabled == is_enabled:
      return
    path = self.base_path + "/enable"
    with open(path, "w") as f:
      f.write("1" if is_enabled else "0")
    self.enabled = is_enabled

  def set_frequency(self, freq):
    """ Set the PWM frequency for all fans connected on this PWM-chip """
    freq = self.clamp_frequency(freq)

    # period is specified in nanoseconds
    period = int((1.0 / float(freq)) * (10**9))
    self.period = period
    path = self.base_path + "/period"

    logging.debug("Setting period to " + str(period) + "ns (freq: " + str(freq) + " Hz)")
    with open(path, "w") as f:
      f.write(str(period))

  def clamp_frequency(self, freq):
    raise NotImplementedError()


class PWM_AM335_Chip_Output(PWM_AM335_Output):
  def __init__(self, base_path):
    super(PWM_AM335_Chip_Output, self).__init__(base_path)

  def clamp_frequency(self, freq):
    if freq < 1000:
      logging.warning("Frequency too low ({} Hz), clamping to 1000 Hz for chip, {}".format(
          freq, self.base_path))
      return 1000
    return freq


class PWM_AM335_Timer_Output(PWM_AM335_Output):
  def __init__(self, base_path):
    super(PWM_AM335_Timer_Output, self).__init__(base_path)

  def clamp_frequency(self, freq):
    if freq > 1000:
      logging.warning("Frequency too high ({} Hz), clamping to 1000 Hz for timer, {}".format(
          freq, self.base_path))
      return 1000
    return freq


class PWM_AM335(object):

  claimed_pins = []

  def get_output(self, chip, channel):
    pin = '{}:{}'.format(chip, channel)
    logging.debug("PWM_AM335: Setting up pin {}".format(pin))

    if pin in PWM_AM335.claimed_pins:
      logging.error("PWM_AM335: Trying to add pin {}, but it has already been added".format(pin))
      raise RuntimeError(
          "PWM_AM335: Trying to add pin {}, but it has already been added".format(pin))
    else:
      self.claimed_pins.append(pin)

    base_path = self._export_chip(chip, channel)

    if chip in [0, 1, 2, 3]:    # TODO these can change - we need to check by device name
      return PWM_AM335_Timer_Output(base_path)
    else:
      return PWM_AM335_Chip_Output(base_path)

  def get_output_by_device(self, device_name, channel):
    paths = glob.glob("/sys/bus/platform/devices/{}/pwm/pwmchip*".format(device_name))
    if len(paths) != 1:
      raise RuntimeError("Could not find PWM by device name {}".format(device_name))

    chip_string = os.path.basename(paths[0])
    chip_number = int(chip_string[7:])
    logging.debug("PWM_AM335: device %s mapped to chip %d", device_name, chip_number)
    return self.get_output(chip_number, channel)

  def _export_chip(self, chip, channel):
    base_path = "/sys/class/pwm/pwmchip{}/pwm-{}:{}".format(chip, chip, channel)
    if not os.path.exists(base_path):
      with open("/sys/class/pwm/pwmchip{}/export".format(chip), "w") as f:
        f.write(str(channel))
      if not os.path.exists(base_path):
        raise RuntimeError("Unable to export PWM pin")
    return base_path
