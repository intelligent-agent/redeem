import logging
import glob
import struct
import time

from redeem.Enable import Enable
from redeem.EndStop import EndStop
from redeem.Key_pin import Key_pin, Key_pin_listener
from redeem.Mosfet import Mosfet
from redeem.Fan import Fan
from redeem.GPIO import AM335x_GPIO_Controller
from redeem.PWM import PWM_AM335
from redeem.Stepper_TMC2130 import StepperBankSpi, Stepper_TMC2130

import redeem.SPI as SPI


def probe_revolve(printer):
  results = find_revolve()
  if results == None:
    logging.warn("No revolve found")
    return

  eeprom_path, eeprom_data, revision = results
  revolve_key = get_revolve_key(eeprom_path, eeprom_data)
  build_revolve_printer(printer, revision)


def find_revolve():
  found = False
  revision = None
  eeprom_data = None
  eeprom_path = None

  nvmem_path = "/sys/bus/nvmem/devices/0-00500/nvmem"
  try:
    with open(nvmem_path, "rb") as f:
      data = f.read(120)
      name = data[5:16].strip()
      if name == "335RVLV00A0":    # TODO what about this can be generally recognized?
        revision = data[12:16]
        eeprom_data = data
        eeprom_path = nvmem_path
        found = True
  except IOError:
    pass

  if not found:
    return None

  logging.debug("Found revolve revision %s at %s", revision, eeprom_path)
  return eeprom_path, eeprom_data, revision


def get_revolve_key(eeprom_path, eeprom_data):
  """ Get the generated key from the config or create one """
  revolve_key = "".join(struct.unpack('7c',
                                      eeprom_data[5:12]))    # TODO this is probably wrong as well
  logging.debug("Found revolve key: '" + revolve_key + "'")
  if revolve_key == '\x00' * 7:
    logging.debug("revolve key invalid")
    import random
    import string
    revolve_key = ''.join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(7))
    eeprom_data = eeprom_data[0:5] + revolve_key + eeprom_data[12:]
    logging.debug("New revolve key: '" + revolve_key + "'")
    try:
      with open(eeprom_path, "wb") as f:
        f.write(eeprom_data[:120])
    except IOError as e:
      logging.warning("Unable to write new key to EEPROM")
  return revolve_key


def build_revolve_printer(printer, revision):
  printer.NUM_AXES = 6
  printer.board = "revolve"
  printer.revision = revision

  gpio = AM335x_GPIO_Controller()

  pwm = PWM_AM335()

  # Enable PWM and steppers
  printer.enable = Enable(gpio.output(0, 18), False)
  printer.enable.set_disabled()
  time.sleep(1)
  printer.enable.set_enabled()
  time.sleep(1)

  # Init the end stops
  EndStop.inputdev = "/dev/input/by-path/platform-gpio_keys-event"
  Key_pin.listener = Key_pin_listener(EndStop.inputdev)

  printer.end_stop_inputs["X1"] = gpio.input(1, 28)
  printer.end_stop_inputs["X2"] = gpio.input(1, 17)
  printer.end_stop_inputs["Y1"] = gpio.input(1, 27)
  printer.end_stop_inputs["Y2"] = gpio.input(1, 29)
  printer.end_stop_inputs["Z1"] = gpio.input(1, 14)
  printer.end_stop_inputs["Z2"] = gpio.input(1, 15)

  printer.end_stop_keycodes["X1"] = 112
  printer.end_stop_keycodes["X2"] = 113
  printer.end_stop_keycodes["Y1"] = 114
  printer.end_stop_keycodes["Y2"] = 115
  printer.end_stop_keycodes["Z1"] = 116
  printer.end_stop_keycodes["Z2"] = 117

  spi = SPI.get_spi_bus_by_device("48030000.spi", 0)

  stepper_bank = StepperBankSpi(spi, 6)

  printer.steppers["X"] = Stepper_TMC2130(
      gpio.output(3, 14), gpio.output(3, 15), gpio.input(0, 27), "X", stepper_bank, 0)
  printer.steppers["Y"] = Stepper_TMC2130(
      gpio.output(3, 16), gpio.output(3, 17), gpio.input(2, 0), "Y", stepper_bank, 1)
  printer.steppers["Z"] = Stepper_TMC2130(
      gpio.output(3, 18), gpio.output(3, 19), gpio.input(1, 16), "Z", stepper_bank, 2)
  printer.steppers["E"] = Stepper_TMC2130(
      gpio.output(3, 20), gpio.output(3, 21), gpio.input(2, 1), "E", stepper_bank, 3)
  printer.steppers["H"] = Stepper_TMC2130(
      gpio.output(2, 26), gpio.output(2, 27), gpio.input(0, 29), "H", stepper_bank, 4)
  printer.steppers["A"] = Stepper_TMC2130(
      gpio.output(2, 28), gpio.output(2, 29), gpio.input(0, 26), "A", stepper_bank, 5)

  for axis, stepper in printer.steppers.iteritems():
    stepper.initialize_registers()
    stepper.sanity_test()

  stepper_bank.start_watcher_thread()

  printer.mosfets["E"] = Mosfet(pwm.get_output_by_device("pwm-heater-e", 0))
  printer.mosfets["H"] = Mosfet(pwm.get_output_by_device("pwm-heater-h", 0))
  printer.mosfets["A"] = Mosfet(pwm.get_output_by_device("pwm-heater-a", 0))
  printer.mosfets["HBP"] = Mosfet(pwm.get_output_by_device("pwm-heater-hbp", 0))

  printer.thermistor_inputs["E"] = "/sys/bus/iio/devices/iio:device0/in_voltage0_raw"
  printer.thermistor_inputs["H"] = "/sys/bus/iio/devices/iio:device0/in_voltage1_raw"
  printer.thermistor_inputs["A"] = "/sys/bus/iio/devices/iio:device0/in_voltage3_raw"
  printer.thermistor_inputs["HBP"] = "/sys/bus/iio/devices/iio:device0/in_voltage2_raw"

  printer.fans.append(Fan(pwm.get_output_by_device("48302200.pwm", 0)))
  printer.fans.append(Fan(pwm.get_output_by_device("48302200.pwm", 1)))
  printer.fans.append(Fan(pwm.get_output_by_device("48304200.pwm", 0)))
  printer.fans.append(Fan(pwm.get_output_by_device("48304200.pwm", 1)))
