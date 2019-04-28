"""
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

import logging
import os
from six import PY2
import struct
if PY2:
  from ConfigParser import SafeConfigParser as Parser
else:
  from configparser import ConfigParser as Parser

class CascadingConfigParser(Parser):
  def __init__(self, config_files):

    Parser.__init__(self)

    # Write options in the case it was read.
    # self.optionxform = str

    # Parse to real path
    self.config_files = []
    for config_file in config_files:
      self.config_files.append(os.path.realpath(config_file))
      self.config_location = os.path.dirname(os.path.realpath(config_file))

    # Parse all config files in list
    for config_file in self.config_files:
      if os.path.isfile(config_file):
        logging.info("Using config file " + config_file)
        if PY2:
          self.readfp(open(config_file))
        else:
          self.read_file(open(config_file))
      else:
        logging.warning("Missing config file " + config_file)
        # Might also add command line options for overriding stuff

  def get_default_settings(self):
    fs = []
    for config_file in self.config_files:
      if os.path.isfile(config_file):
        c_file = os.path.basename(config_file)
        cp = Parser()
        if PY2:
          cp.readfp(open(config_file))
        else:
          cp.read_file(open(config_file))
        fs.append((c_file, cp))

    lines = []
    for section in self.sections():
      for option in self.options(section):
        for (name, cp) in fs:
          if cp.has_option(section, option):
            line = [name, section, option, cp.get(section, option)]
        lines.append(line)

    return lines

  def save(self, filename):
    """ Save the changed settings to local.cfg """
    current = CascadingConfigParser(self.config_files)

    # Build a list of changed values
    to_save = []
    for section in self.sections():
      #logging.debug(section)
      for option in self.options(section):
        if self.get(section, option) != current.get(section, option):
          old = current.get(section, option)
          val = self.get(section, option)
          to_save.append((section, option, val, old))

    # Update local config with changed values
    local = Parser()
    # Start each file with revision identification
    local.add_section("Configuration")
    local.set("Configuration", "version", "1")
    if PY2:
      local.readfp(open(filename))
    else:
      local.read_file(open(filename))
    for opt in to_save:
      (section, option, value, old) = opt
      if not local.has_section(section):
        local.add_section(section)
      local.set(section, option, value)
      logging.info("Update setting: {} from {} to {} ".format(option, old, value))

    # Save changed values to file
    local.write(open(filename, "w+"))

  def check(self, filename):
    """ Check the settings currently set against default.cfg """
    default = Parser()
    if PY2:
      default.readfp(open(os.path.join(self.config_location, "default.cfg")))
    else:
      default.read_file(open(os.path.join(self.config_location, "default.cfg")))
    local = Parser()

    if PY2:
      local.readfp(open(filename))
    else:
      local.read_file(open(filename))

    local_ok = True
    diff = set(local.sections()) - set(default.sections())
    for section in diff:
      logging.warning("Section {} does not exist in {}".format(section, "default.cfg"))
      local_ok = False
    for section in local.sections():
      if not default.has_section(section):
        continue
      diff = set(local.options(section)) - set(default.options(section))
      for option in diff:
        logging.warning("Option {} in section {} does not exist in {}".format(
            option, section, "default.cfg"))
        local_ok = False
    if local_ok:
      logging.info("{} is OK".format(filename))
    else:
      logging.warning("{} contains errors.".format(filename))
    return local_ok
