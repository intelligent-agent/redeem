import logging
import glob
import struct
import subprocess

from redeem.PWM import PWM_PCA9685
from redeem.Enable import Enable
from redeem.EndStop import EndStop
from redeem.Stepper import Stepper_00A3, Stepper_00A4, Stepper_00B1, Stepper_00B2, Stepper_00B3
from redeem.Key_pin import Key_pin, Key_pin_listener
from redeem.Mosfet import Mosfet
from redeem.Fan import Fan
from redeem.GPIO import AM335x_GPIO_Controller
from redeem.DAC import DAC, PWM_DAC

import redeem.SPI as SPI


def probe_replicape(printer):
  results = find_replicape()
  if results == None:
    logging.warn("No replicape found")
    return

  eeprom_path, eeprom_data, revision = results
  key = get_replicape_key(eeprom_path, eeprom_data)
  build_replicape_printer(printer, revision, key)


def find_replicape():
  found = False
  revision = None
  eeprom_data = None
  eeprom_path = None

  nvmem_paths = glob.glob("/sys/bus/nvmem/devices/[1-2]-005[4-7]0/nvmem")
  for i, nvmem_path in enumerate(nvmem_paths):
    try:
      with open(nvmem_path, "rb") as f:
        data = f.read(120)
        name = data[58:74].strip()
        if name == "BB-BONE-REPLICAP":
          revision = data[38:42]
          eeprom_data = data
          eeprom_path = nvmem_path
          found = True
          break
    except IOError:
      pass

  if not found:
    return None

  logging.debug("Found replicape revision %s at %s", revision, eeprom_path)
  return eeprom_path, eeprom_data, revision


def get_replicape_key(eeprom_path, eeprom_data):
  """ Get the generated key from the config or create one """
  key = "".join(struct.unpack('20c', eeprom_data[100:120]))
  logging.debug("Found Replicape key: '" + key + "'")
  if key == '\x00' * 20:
    logging.debug("Replicape key invalid")
    import random
    import string
    key = ''.join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(20))
    eeprom_data = eeprom_data[:100] + key
    logging.debug("New Replicape key: '" + key + "'")
    try:
      with open(eeprom_path, "wb") as f:
        f.write(eeprom_data[:120])
    except IOError as e:
      logging.warning("Unable to write new key to EEPROM")
  return key


def build_replicape_printer(printer, revision, key):
  printer.NUM_AXES = 5
  printer.board = "replicape"
  printer.revision = revision
  printer.key = key

  gpio = AM335x_GPIO_Controller()

  # first get the PWM controller
  kernel_version = subprocess.check_output(["uname", "-r"]).strip()
  [major, minor, rev] = kernel_version.split("-")[0].split(".")
  if (int(major) == 3 and int(minor) >= 14) or int(major) > 3:
    pwm = PWM_PCA9685(0x70, 2)
  else:
    pwm = PWM_PCA9685(0x70, 1)

  if revision in ["00A4", "0A4A", "00A3"]:
    pwm.set_frequency(100)
  elif revision in ["00B1", "00B2", "00B3", "0B3A"]:
    pwm.set_frequency(1000)

  # Enable PWM and steppers
  printer.enable = Enable(gpio.output(0, 20), True)
  printer.enable.set_disabled()

  # Init the end stops
  EndStop.inputdev = "/dev/input/by-path/platform-ocp:gpio_keys-event"
  Key_pin.listener = Key_pin_listener(EndStop.inputdev)

  printer.end_stop_inputs["X1"] = gpio.input(3, 21)
  printer.end_stop_inputs["X2"] = gpio.input(0, 30)
  printer.end_stop_inputs["Y1"] = gpio.input(1, 17)

  if revision == "0A4A":    #TODO verify - this is based on a comment formerly in default.cfg
    printer.end_stop_inputs["Y2"] = gpio.input(1, 19)
  else:
    printer.end_stop_inputs["Y2"] = gpio.input(3, 17)

  printer.end_stop_inputs["Z1"] = gpio.input(0, 31)
  printer.end_stop_inputs["Z2"] = gpio.input(0, 4)

  printer.end_stop_keycodes["X1"] = 112
  printer.end_stop_keycodes["X2"] = 113
  printer.end_stop_keycodes["Y1"] = 114
  printer.end_stop_keycodes["Y2"] = 115
  printer.end_stop_keycodes["Z1"] = 116
  printer.end_stop_keycodes["Z2"] = 117

  if revision == "00A3":
    printer.steppers["X"] = Stepper_00A3(
        gpio.output(0, 27), gpio.output(1, 29), gpio.input(2, 4), 0, "X")
    printer.steppers["Y"] = Stepper_00A3(
        gpio.output(1, 12), gpio.output(0, 22), gpio.input(2, 5), 1, "Y")
    printer.steppers["Z"] = Stepper_00A3(
        gpio.output(0, 23), gpio.output(0, 26), gpio.input(0, 15), 2, "Z")
    printer.steppers["E"] = Stepper_00A3(
        gpio.output(1, 28), gpio.output(1, 15), gpio.input(2, 1), 3, "E")
    printer.steppers["H"] = Stepper_00A3(
        gpio.output(1, 13), gpio.output(1, 14), gpio.input(2, 3), 4, "H")
  elif revision == "00B1":
    printer.steppers["X"] = Stepper_00B1(
        gpio.output(0, 27), gpio.output(1, 29), gpio.input(2, 4), PWM_DAC(pwm.get_output(11)), 0,
        "X")
    printer.steppers["Y"] = Stepper_00B1(
        gpio.output(1, 12), gpio.output(0, 22), gpio.input(2, 5), PWM_DAC(pwm.get_output(12)), 1,
        "Y")
    printer.steppers["Z"] = Stepper_00B1(
        gpio.output(0, 23), gpio.output(0, 26), gpio.input(0, 15), PWM_DAC(pwm.get_output(13)), 2,
        "Z")
    printer.steppers["E"] = Stepper_00B1(
        gpio.output(1, 28), gpio.output(1, 15), gpio.input(2, 1), PWM_DAC(pwm.get_output(14)), 3,
        "E")
    printer.steppers["H"] = Stepper_00B1(
        gpio.output(1, 13), gpio.output(1, 14), gpio.input(2, 3), PWM_DAC(pwm.get_output(15)), 4,
        "H")
  elif revision == "00B2":
    printer.steppers["X"] = Stepper_00B2(
        gpio.output(0, 27), gpio.output(1, 29), gpio.input(2, 4), PWM_DAC(pwm.get_output(11)), 0,
        "X")
    printer.steppers["Y"] = Stepper_00B2(
        gpio.output(1, 12), gpio.output(0, 22), gpio.input(2, 5), PWM_DAC(pwm.get_output(12)), 1,
        "Y")
    printer.steppers["Z"] = Stepper_00B2(
        gpio.output(0, 23), gpio.output(0, 26), gpio.input(0, 15), PWM_DAC(pwm.get_output(13)), 2,
        "Z")
    printer.steppers["E"] = Stepper_00B2(
        gpio.output(1, 28), gpio.output(1, 15), gpio.input(2, 1), PWM_DAC(pwm.get_output(14)), 3,
        "E")
    printer.steppers["H"] = Stepper_00B2(
        gpio.output(1, 13), gpio.output(1, 14), gpio.input(2, 3), PWM_DAC(pwm.get_output(15)), 4,
        "H")
  elif revision in ["00B3", "0B3A"]:
    printer.steppers["X"] = Stepper_00B3(
        gpio.output(0, 27), gpio.output(1, 29), 90, PWM_DAC(pwm.get_output(11)), 0, "X")
    printer.steppers["Y"] = Stepper_00B3(
        gpio.output(1, 12), gpio.output(0, 22), 91, PWM_DAC(pwm.get_output(12)), 1, "Y")
    printer.steppers["Z"] = Stepper_00B3(
        gpio.output(0, 23), gpio.output(0, 26), 92, PWM_DAC(pwm.get_output(13)), 2, "Z")
    printer.steppers["E"] = Stepper_00B3(
        gpio.output(1, 28), gpio.output(1, 15), 93, PWM_DAC(pwm.get_output(14)), 3, "E")
    printer.steppers["H"] = Stepper_00B3(
        gpio.output(1, 13), gpio.output(1, 14), 94, PWM_DAC(pwm.get_output(15)), 4, "H")
  elif revision in ["00A4", "0A4A"]:
    dac_spi = SPI.get_spi_bus_by_device("481a0000.spi", 0)
    printer.steppers["X"] = Stepper_00A4(
        gpio.output(0, 27), gpio.output(1, 29), gpio.input(2, 4), DAC(dac_spi, 0), 0, "X")
    printer.steppers["Y"] = Stepper_00A4(
        gpio.output(1, 12), gpio.output(0, 22), gpio.input(2, 5), DAC(dac_spi, 1), 1, "Y")
    printer.steppers["Z"] = Stepper_00A4(
        gpio.output(0, 23), gpio.output(0, 26), gpio.input(0, 15), DAC(dac_spi, 2), 2, "Z")
    printer.steppers["E"] = Stepper_00A4(
        gpio.output(1, 28), gpio.output(1, 15), gpio.input(2, 1), DAC(dac_spi, 3), 3, "E")
    printer.steppers["H"] = Stepper_00A4(
        gpio.output(1, 13), gpio.output(1, 14), gpio.input(2, 3), DAC(dac_spi, 4), 4, "H")

  printer.mosfets["E"] = Mosfet(pwm.get_output(5))
  printer.mosfets["H"] = Mosfet(pwm.get_output(3))
  printer.mosfets["HBP"] = Mosfet(pwm.get_output(4))

  printer.thermistor_inputs["E"] = "/sys/bus/iio/devices/iio:device0/in_voltage4_raw"
  printer.thermistor_inputs["H"] = "/sys/bus/iio/devices/iio:device0/in_voltage5_raw"
  printer.thermistor_inputs["HBP"] = "/sys/bus/iio/devices/iio:device0/in_voltage6_raw"

  # Init the three fans. Argument is PWM channel number
  printer.fans = []
  if printer.revision == "00A3":
    printer.fans.append(Fan(pwm.get_output(0)))
    printer.fans.append(Fan(pwm.get_output(1)))
    printer.fans.append(Fan(pwm.get_output(2)))
  elif printer.revision == "0A4A":
    printer.fans.append(Fan(pwm.get_output(8)))
    printer.fans.append(Fan(pwm.get_output(9)))
    printer.fans.append(Fan(pwm.get_output(10)))
  elif printer.revision in ["00B1", "00B2", "00B3", "0B3A"]:
    printer.fans.append(Fan(pwm.get_output(7)))
    printer.fans.append(Fan(pwm.get_output(8)))
    printer.fans.append(Fan(pwm.get_output(9)))
    printer.fans.append(Fan(pwm.get_output(10)))
