import logging
import os.path


class GPIO_Output_Pin:
  def __init__(self, file, chip, pin):
    self.file = file
    self.chip = chip
    self.pin = pin

  def enable(self):
    self.file.write("1\n")
    self.file.flush()

  def disable(self):
    self.file.write("0\n")
    self.file.flush()

  def get_chip(self):
    return self.chip

  def get_pin(self):
    return self.pin


class GPIO_Input_Pin:
  def __init__(self, file, chip, pin):
    self.file = file
    self.chip = chip
    self.pin = pin

  def get_chip(self):
    return self.chip

  def get_pin(self):
    return self.pin

  # TODO this is currently a stub because we don't actually use our input GPIOs directly


class AM335x_GPIO_Controller:
  def _get_pin_number(self, chip, pin):
    return chip * 32 + pin

  def _export_pin(self, pin_number):
    if os.path.isdir("/sys/class/gpio/gpio{}".format(pin_number)):
      return

    try:
      with open("/sys/class/gpio/export", "w") as f:
        f.write("{}\n".format(pin_number))
    except IOError as e:
      logging.warning("Failed to init gpio{}, probably expected: {}".format(pin_number, e))

  def _set_direction(self, pin_number, direction):
    try:
      with open("/sys/class/gpio/gpio{}/direction".format(pin_number), "r") as f:
        current_direction = f.read().strip()
        if current_direction == direction:
          return
      with open("/sys/class/gpio/gpio{}/direction".format(pin_number), "w") as f:
        f.write(direction + "\n")
    except IOError as e:
      logging.warning("Failed to set direction on gpio{}, probably expected: {}".format(
          pin_number, e))

  def output(self, chip, pin):
    pin_number = self._get_pin_number(chip, pin)

    self._export_pin(pin_number)
    self._set_direction(pin_number, "out")
    return GPIO_Output_Pin(open("/sys/class/gpio/gpio{}/value".format(pin_number), "w"), chip, pin)

  def input(self, chip, pin):
    pin_number = self._get_pin_number(chip, pin)

    self._export_pin(pin_number)
    self._set_direction(pin_number, "in")
    return GPIO_Input_Pin(None, chip, pin)
