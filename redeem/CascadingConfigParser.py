"""
Author: Elias Bakken & Daryl Bond
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

from configobj import OPTION_DEFAULTS, ConfigObj, Section
import os
import logging
import struct
import copy

#==============================================================================
# Functions
#==============================================================================

def walk_up(section, lineage):
    '''return the parentage of a section in list form'''
    if section.depth == 1:
        return lineage
    else:
        lineage.insert(0, section.parent.name)
        walk_up(section.parent, lineage)
    return lineage

def walk_down(cfg, path, key, value, allow_new):
    '''make/modify an entry of value in a dict given a list of sections and a 
    key. New sections only allowed in allow_new'''
    
    if allow_new == True:
        allow = True
    else:
        allow = False
        for p in reversed(path):
            if p in allow_new:
                allow = True
                break
    
    if cfg.depth >= len(path):

        # check if we can add a value
        if key not in cfg:
            if not allow:
                return True
        
        cfg[key] = value
        return False
    else:
        # check if we can add a section
        if path[cfg.depth] not in cfg:
            if allow:
                cfg[path[cfg.depth]] = {}
            else:
                return True
                
        return walk_down(cfg[path[cfg.depth]], path, key, value, allow_new)


def check_modified(cfg, path, key, value):
    '''check if value is the same as that in a dict given a list of 
    sections and a key'''
    
    if cfg.depth >= len(path):
        if cfg[key] != value:
            return True
        return False
    else:
        if path[cfg.depth] not in cfg:
            return True
        else:
            modified = check_modified(cfg[path[cfg.depth]], path, key, value)
    return modified

#==============================================================================
# Class
#==============================================================================

class CascadingConfigParser(ConfigObj):
    """
    Build a configuration from a hierarchy of inputs where each successive
    input is allowed to overwrite the ones before
    """
    
    parser_options = OPTION_DEFAULTS
    
    def __init__(self, config_files, allow_new=[]):
        """
        initialize the config parser
        
        config_files: list of paths to config files
        allow_new: a list of sections that permit children to be added 
            regardless of whether those children existed in the first 
            config file 
        """
        
        self.parser_options["list_values"] = False

        ConfigObj.__init__(self)
        
        # sections which are allowed to have entries added by printer.cfg, or local.cfg
        self.allow_new = allow_new

        # Parse to real path
        self.config_files = []
        for config_file in config_files:
            self.config_files.append(os.path.realpath(config_file))
            self.config_location = os.path.dirname(os.path.realpath(config_file))

        # check all config files in list
        for config_file in self.config_files:
            if os.path.isfile(config_file):
                logging.info("Using config file " + config_file)
                self.readfp(open(config_file))
            else:
                logging.warning("Missing config file " + config_file)
        
        # parse config files
        self.load()    

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
        
        # get a copy of the currently hard-coded configs
        current = CascadingConfigParser(self.config_files)
        
        # get a flat list of all entries in the live config
        items = []
        self.walk(lambda section, key : items.append(
            (walk_up(section,[section.name]), key, section[key])))   
        
        # check for differences between the live config and the hard config
        to_save = []
        for item in items:
            if check_modified(current, item[0], item[1], item[2]):
                to_save.append(item)
        
        # make a new temporary config object and load in the stuff to be saved
        local = ConfigObj(**self.parser_options)
        for item in to_save:
            walk_down(local, item[0], item[1], item[2], allow_new=True)
            
            path = '-'.join(item[0]+[item[1]])
            logging.info("Update local config: {} = {} ".format(path, item[2]))
            
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
        
    def getint(self, *path):
        ''' get integer '''
        cfg = self
        for s in path[:-1]:
            cfg = cfg[s]
        return cfg.as_int(path[-1])
    
    def getfloat(self, *path):
        ''' get float '''
        cfg = self
        for s in path[:-1]:
            cfg = cfg[s]
        return cfg.as_float(path[-1])
        
    def getboolean(self, *path):
        ''' get integer '''
        cfg = self
        for s in path[:-1]:
            cfg = cfg[s]
        return cfg.as_bool(path[-1])
        
    def get(self, *path):
        ''' get whatever is there '''
        cfg = self
        for s in path[:-1]:
            cfg = cfg[s]
        return cfg[path[-1]]
        
    def has_option(self, *path):
        '''check if path exists'''
        cfg = self
        try:
            for s in path:
                cfg = cfg[s]
        except:
            return False
            
        if not isinstance(cfg, Section):
            return True
        return False
            
    def has_section(self, *path):
        '''check for section'''
        cfg = self
        try:
            for s in path:
                cfg = cfg[s]
        except:
            return False
        
        if isinstance(cfg, Section):
            return True
            
        return False
