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
                logging.info("Using config file "+config_file)        
                self.readfp(open(config_file))              
            else:
                logging.warning("Missing config file "+config_file)        
        
        # Might also add command line options for overriding stuff

    ''' Get the largest (newest) timestamp for all the config files. '''
    def timestamp(self):
        ts = 0 
        for config_file in self.config_files:
            if os.path.isfile(config_file):                    
                ts = max(ts, os.path.getmtime(config_file))
        return ts

