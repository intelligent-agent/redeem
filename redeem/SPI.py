import glob
import os.path
import logging


def get_spi_bus_by_device(bus_name, device_number):
  paths = glob.glob("/sys/bus/platform/devices/{}/spi_master/spi*".format(bus_name))
  if len(paths) != 1:
    raise RuntimeError("Could not find SPI by bus name {}".format(bus_name))

  bus_number = int(os.path.basename(paths[0])[3:])

  logging.debug("SPI bus %s mapped to number %d, so we're opening spi%d_%d", bus_name, bus_number,
                bus_number, device_number)

  import spidev
  bus = spidev.SpiDev()
  bus.open(bus_number, device_number)

  return bus
