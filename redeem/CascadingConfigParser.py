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


class CascadingConfigParser(ConfigParser.SafeConfigParser):
    def __init__(self, config_files):

        ConfigParser.SafeConfigParser.__init__(self)

        # Parse to real path
        self.config_files = []
        for config_file in config_files:
            self.config_files.append(os.path.realpath(config_file))

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
        
        if os.path.islink("/etc/redeem/printer.cfg"):
            ts = max(ts, os.lstat("/etc/redeem/printer.cfg").st_mtime)
        return ts

    def parse_capes(self):
        """ Read the name and revision of each cape on the BeagleBone """
        self.replicape_revision = None
        self.reach_revision = None
        for busNumber in ["1","2"]:
            for addr in ["4", "5", "6", "7"]:
                path = "/sys/bus/i2c/devices/"+busNumber+"-005"+addr
                if(os.path.isfile(path+"/eeprom")):
                    eeprom = path+"/eeprom"
                elif os.path.isfile(path+"/nvmem/at24-1/nvmem"):
                    eeprom = path+"/nvmem/at24-1/nvmem"
                elif os.path.isfile(path+"/at24-1/nvmem"):
                    eeprom = path+"/at24-1/nvmem"
                else:
                    continue
                try:
                    with open(eeprom, "rb") as f:
                        data = f.read(100)
                        name = data[58:74].strip()
                        if name == "BB-BONE-REPLICAP":
                            self.replicape_revision = data[38:42]
                        elif name[:13] == "BB-BONE-REACH":
                            self.reach_revision = data[38:42]

                        if self.replicape_revision != None and self.reach_revision != None:
                            break
                except IOError as e:
                    pass

            if self.replicape_revision != None and self.reach_revision != None:
                    break


    
    def save(self, filename):
        """ Save the changed settings to local.cfg """
        current = CascadingConfigParser(self.config_files)

        # Get list of changed values
        to_save = []
        for section in self.sections():
            logging.debug(section)
            for option in self.options(section):                
                if self.get(section, option) != current.get(section, option):
                    logging.info("'"+str(self.get(section, option))+"'")
                    logging.info("'"+str(current.get(section, option))+"'")
                    val = self.get(section, option)
                    to_save.append([section, option, val])

        # Update local config with changed values
        local = ConfigParser.SafeConfigParser()
        local.readfp(open(filename, "r"))
        for opt in to_save:         
            section =  opt[0]
            option = opt[1]
            value = opt[2]
            if not local.has_section(section):
                local.add_section(section)
            local.set(section, option, value)
            logging.info("Update setting: "+option)

                    
        # Save changed values to file
        local.write(open(filename, "w+"))

    
