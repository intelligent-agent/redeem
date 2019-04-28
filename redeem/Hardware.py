# -*- coding: utf-8 -*-
import logging
import struct


def identify_capes(printer_configuration):
  """ Read the name and revision of each cape on the BeagleBone """
  printer_configuration.set('Configuration', 'replicape', "None")
  printer_configuration.set('Configuration', 'reach', "None")
  replicape_data = '\x00' * 120
  replicape_path = None

  import glob
  paths = glob.glob("/sys/bus/i2c/devices/[1-2]-005[4-7]/*/nvmem")
  paths.extend(glob.glob("/sys/bus/i2c/devices/[1-2]-005[4-7]/nvmem/at24-[1-4]/nvmem"))
  #paths.append(glob.glob("/sys/bus/i2c/devices/[1-2]-005[4-7]/eeprom"))
  for i, path in enumerate(paths):
    try:
      with open(path, "rb") as f:
        data = f.read(120)
        name = data[58:74].strip()
        if name == b"BB-BONE-REPLICAP":
          printer_configuration.set('Configuration', 'replicape', data[38:42])
          replicape_data = data
          replicape_path = path
        elif name[:13] == b"BB-BONE-REACH":
          printer_configuration.set('Configuration', 'reach', data[38:42])
          if printer_configuration.get('Configuration', 'replicape') != "None":
            break
    except IOError as e:
      pass
  """ Get the generated key from the config or create one """
  the_cape_key = "".join(struct.unpack('20c', replicape_data[100:120]))
  logging.debug("Found Replicape key: '{}'".format(the_cape_key))
  if the_cape_key == '\x00' * 20:
    logging.debug("Replicape key invalid")
    import random
    import string
    the_cape_key = ''.join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(20))
    replicape_data = replicape_data[:100] + the_cape_key
    logging.debug("New Replicape key: '{}'".format(the_cape_key))
    try:
      if replicape_path:
        with open(replicape_path, "wb") as f:
          f.write(replicape_data[:120])
    except IOError as e:
      logging.warning("Unable to write new key to EEPROM")
  printer_configuration.set('System', 'key', the_cape_key)
