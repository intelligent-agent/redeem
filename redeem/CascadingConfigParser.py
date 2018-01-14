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
    
    parser_options = OPTION_DEFAULTS
    
    def __init__(self, config_files, allow_new=[]):
        
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

    def load(self):
        '''generate a config that combines all of the cascading configs in the 
        list. Config entry (i+1) entry overwrites entry (i). Entries may be 
        added at any level but only in allowed sections'''

        for i, config_file in enumerate(self.config_files):
            if os.path.isfile(config_file):
                c_file = os.path.basename(config_file)
                items = []
                if i == 0: # generate the base config 
                    self._initialise(self.parser_options)
                    self._load(config_file, self._original_configspec)
                    self.default_cfg = self.dict()
                else:
                    cfg = ConfigObj(config_file, **self.parser_options)
                
                    # get a linear list of all items
                    items = []
                    cfg.walk(lambda section, key : items.append(
                        (walk_up(section,[section.name]), key, section[key])))
                    
                    # overwrite or add to the base config
                    for item in items:
                        if walk_down(self, item[0], item[1], item[2], self.allow_new):
                            path = '/'.join(item[0]+[item[1]])
                            msg = "Config entry not permitted : {} = {} ".format(path, item[2])
                            logging.warning(msg)
                        
                
        return

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


if __name__ == '__main__':
    c = CascadingConfigParser(["../configs/default.cfg", "../configs/test.cfg"], allow_new=["Temperature Control"])
    
    print c["Fans"]
    
    #c.save("")
    
    #print c#["Temperature Control"]