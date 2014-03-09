'''
PruFirmware.py file for Replicape. 

Handles the compilation of the PRU firmware based on the different printer settings on the fly.

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

import os
import logging
import subprocess

class PruFirmware:

    def __init__(self, firmware_source_file, binary_filename, revision, config_filename, config_parser,compiler):
        """Create and initialize a PruFirmware

        Parameters
        ----------

        firmware_source_file : string
            The path to the firmware source to use to produce the firmware
        binary_filename : string
            Full path to the file where to store the final firmware file without the extension (without .bin)
        revision : string
            The revision of the board (A3 or A4)
        config_filename : string
            The full path to the configuration file
        config_parser : ConfigParser
            The config parser with the config file already loaded
        compiler : string
            Path to the pasm compiler
        """

        self.firmware_source_file = os.path.realpath(firmware_source_file)
        self.binary_filename = os.path.realpath(binary_filename)
        self.revision = revision
        self.config_filename = os.path.realpath(config_filename)
        self.config = config_parser
        self.compiler = os.path.realpath(compiler)

        #Remove the bin extension of the firmware output filename

        if os.path.splitext(self.binary_filename)[1]!='.bin':
            logging.error('Invalid binary output filename. It should have the .bin extension.')
            raise RuntimeError('Invalid binary output filename. It should have the .bin extension.')

        self.binary_filename_compiler=os.path.splitext(self.binary_filename)[0]

        if not os.path.exists(self.compiler):
            logging.error('PASM compiler not found. Go to the firmware directory and issue the `make` command.')
            raise RuntimeError('PASM compiler not found.')

    def is_needing_firmware_compilation(self):
        if os.path.exists(self.binary_filename):
            #Check if we need to rebuild the firmware
            config_mtime = os.path.getmtime(self.config_filename) #modif time of config file
            fw_mtime = os.path.getmtime(self.binary_filename) #modif time of firmware file
            fw_src_mtime = os.path.getmtime(self.firmware_source_file) #modif time of firmware source file
            if fw_mtime >= config_mtime and fw_mtime>=fw_src_mtime: #already up to date
                return False

        return True

    def produce_firmware(self):
        if not self.is_needing_firmware_compilation():
            return True

        #First setting: end stop inversion

        #FIXME: We support only all inverted or nothing inverted for now in the firmware.
        shouldInvert = self.config.getboolean('Endstops', 'invert_X1')
        shouldInvert |= self.config.getboolean('Endstops', 'invert_X2')
        shouldInvert |= self.config.getboolean('Endstops', 'invert_Y1')
        shouldInvert |= self.config.getboolean('Endstops', 'invert_Y2')
        shouldInvert |= self.config.getboolean('Endstops', 'invert_Z1')
        shouldInvert |= self.config.getboolean('Endstops', 'invert_Z2')

        revision = "-DREV_A3" if self.revision == "A3" else "-DREV_A4"
        
        cmd = [self.compiler,'-b',revision]

        for s in ['x','y','z','e','h']:
            cmd.append('-DSTEPPER_'+s.upper()+'_DIRECTION='+("0" if self.config.getint('Steppers', 'direction_'+s)>0 else "1"))

        

        if shouldInvert:
            cmd.append("-DENDSTOP_INVERSED=1");

        cmd.extend([self.firmware_source_file,self.binary_filename_compiler])

        logging.debug("Compiling firmware with "+' '.join(cmd))
        try:
            subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            logging.debug("Compilation succeeded.")
        except subprocess.CalledProcessError as e:
            logging.exception('Error while compiling firmware: ')
            logging.error('Command output:'+e.output)
            return False

        return True

    ''' Return the path to the firmware bin file, None if the firmware cannot be produced. '''
    def get_firmware(self):
        if not os.path.exists(self.binary_filename) or self.is_needing_firmware_compilation():
            if not self.produce_firmware():
                return None

        return self.binary_filename

    
