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
        self.replicape_revision = None
        self.reach_revision = None

        import glob
        paths = glob.glob("/sys/bus/i2c/devices/[1-2]-005[4-7]/*/nvmem")
        paths.extend(glob.glob("/sys/bus/i2c/devices/[1-2]-005[4-7]/nvmem/at24-[1-4]/nvmem"))
        #paths.append(glob.glob("/sys/bus/i2c/devices/[1-2]-005[4-7]/eeprom"))
        for i, path in enumerate(paths):
            try:
                with open(path, "rb") as f:
                    data = f.read(120)
                    name = data[58:74].strip()
                    if name == "BB-BONE-REPLICAP":
                        self.replicape_revision = data[38:42]
                        self.replicape_data = data
                        self.replicape_path = path
                    elif name[:13] == "BB-BONE-REACH":
                        self.reach_revision = data[38:42]
                        self.reach_data = data
                        self.reach_path = path
                    if self.replicape_revision != None and self.reach_revision != None:
                        break
            except IOError as e:
                pass
        return

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
        self.replicape_key = "".join(struct.unpack('20c', self.replicape_data[100:120]))
        logging.debug("Found Replicape key: '"+self.replicape_key+"'")
        if self.replicape_key == '\x00'*20:
            logging.debug("Replicape key invalid")
            import random
            import string
            self.replicape_key = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(20))
            self.replicape_data = self.replicape_data[:100] + self.replicape_key
            logging.debug("New Replicape key: '"+self.replicape_key+"'")
            #logging.debug("".join(struct.unpack('20c', self.new_replicape_data[100:120])))
            try:
                with open(self.replicape_path, "wb") as f:
                    f.write(self.replicape_data[:120])
            except IOError as e:
                logging.warning("Unable to write new key to EEPROM")
        return self.replicape_key


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')
    c = CascadingConfigParser(["/etc/redeem/default.cfg", "/etc/redeem/printer.cfg", "/etc/redeem/local.cfg"])
    print(c.get_default_settings())
