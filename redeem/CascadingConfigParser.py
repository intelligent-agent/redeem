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

import ConfigParser
import os
import logging
import struct


class CascadingConfigParser(ConfigParser.SafeConfigParser):
    def __init__(self, config_files):

        ConfigParser.SafeConfigParser.__init__(self)

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
                self.readfp(open(config_file))
            else:
                logging.warning("Missing config file " + config_file)
                # Might also add command line options for overriding stuff

    def timestamp(self):
        """ Get the largest (newest) timestamp for all the config files. """
        ts = 0
        for config_file in self.config_files:
            if os.path.isfile(config_file):
                ts = max(ts, os.path.getmtime(config_file))

        printer_cfg = os.path.join(self.config_location, "printer.cfg")
        if os.path.islink(printer_cfg):
            ts = max(ts, os.lstat(printer_cfg).st_mtime)
        return ts

    def parse_capes(self):
        """ Read the name and revision of each cape on the BeagleBone """
        self.board_name = None
        self.board_rev  = None
        self.cape_name  = None
        self.cape_rev   = None
        self.addon_name = None
        self.addon_rev  = None
        self.key_path   = None

        # Get baseboard
        with open("/sys/devices/platform/bone_capemgr/baseboard/board-name", "r") as f:
            self.board_name = f.readline().rstrip()
        with open("/sys/devices/platform/bone_capemgr/baseboard/revision", "r") as f:
            self.board_rev = f.readline().rstrip()

        logging.info("Found board '{}', rev '{}'".format(self.board_name, self.board_rev))

        # Revolve has the key stored in base board EEPROM
        if self.board_name == "A335RVLV": 
            logging.info("Baseboard is Revolve, board revision {}".format(self.board_rev))
            self.board_name = "Revolve"
            self.key_path = "/sys/bus/i2c/devices/0-0050/eeprom"
        else:
            for i in range(4):
                name_path = "/sys/devices/platform/bone_capemgr/slot-{}/board-name".format(i)
                rev_path  = "/sys/devices/platform/bone_capemgr/slot-{}/revision".format(i)
                if os.path.isfile(name_path):
                    with open(name_path) as f:
                        name = f.readline()
                    if name.startswith("Replicape"):
                        self.cape_name = "Replicape"
                        self.key_path = "/sys/bus/i2c/devices/0-00{}/eeprom".format(50+i)
                        with open(rev_path) as f:
                            self.cape_rev = f.readline()
                    elif name.startswith("Reach"):
                        self.addon_name = "Reach"
                        with open(rev_path) as f:
                            self.addon_rev = f.readline()    

        if self.key_path:
            logging.debug("Checking for key at {}".format(self.key_path))            
            with open(self.key_path, "rb") as f:
                self.key_data = f.read(120)
            self.replicape_key = "".join(struct.unpack('20c', self.key_data[100:120]))
            if self.replicape_key == '\x00'*20 or self.replicape_key == '\xFF'*20:
                logging.debug("Replicape key invalid")
                self.replicape_key = self.make_key()
                self.replicape_data = self.key_data[:100] + self.replicape_key
                logging.debug("New Replicape key: '"+self.replicape_key+"'")
                try:
                    with open(self.key_path, "wb") as f:
                        f.write(self.key_data[:120])
                except IOError as e:
                    logging.warning("Unable to write new key to EEPROM")
            else:
                logging.debug("Found Replicape key : '{}'".format(self.replicape_key))

        else:
            self.replicape_key = self.make_key()
            logging.debug("Using random key: '"+self.replicape_key+"'")

    def get_default_settings(self):
        fs = []
        for config_file in self.config_files:
            if os.path.isfile(config_file):
                c_file = os.path.basename(config_file)
                cp = ConfigParser.SafeConfigParser()
                cp.readfp(open(config_file))
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

        # Get list of changed values
        to_save = []
        for section in self.sections():
            #logging.debug(section)
            for option in self.options(section):
                if self.get(section, option) != current.get(section, option):
                    old = current.get(section, option)
                    val = self.get(section, option)
                    to_save.append((section, option, val, old))

        # Update local config with changed values
        local = ConfigParser.SafeConfigParser()
        local.readfp(open(filename, "r"))
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
        default = ConfigParser.SafeConfigParser()
        default.readfp(open(os.path.join(self.config_location, "default.cfg")))
        local   = ConfigParser.SafeConfigParser()
        local.readfp(open(filename))

        local_ok = True
        diff = set(local.sections())-set(default.sections())
        for section in diff:
            logging.warning("Section {} does not exist in {}".format(section, "default.cfg"))
            local_ok = False
        for section in local.sections():
            if not default.has_section(section):
                continue
            diff = set(local.options(section))-set(default.options(section))
            for option in diff:
                logging.warning("Option {} in section {} does not exist in {}".format(option, section, "default.cfg"))
                local_ok = False
        if local_ok:
            logging.info("{} is OK".format(filename))
        else:
            logging.warning("{} contains errors.".format(filename))
        return local_ok

    def get_key(self):
        """ Get the generated key from the config or create one """
        return self.replicape_key


    def make_key(self):
        import random
        import string
        return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(20))

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')
    c = CascadingConfigParser(["/etc/redeem/default.cfg", "/etc/redeem/printer.cfg", "/etc/redeem/local.cfg"])
    print(c.get_default_settings())
