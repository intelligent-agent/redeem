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

    def __init__(self, firmware_source_file0, binary_filename0, revision, config_filename, config_parser,compiler):
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

        
        firmware_source_file1 = "/usr/src/redeem/firmware/firmware_endstops.p"
        binary_filename1 = "/usr/src/redeem/firmware/firmware_endstops.bin"
    
        self.firmware_source_file0 = os.path.realpath(firmware_source_file0)
        self.firmware_source_file1 = os.path.realpath(firmware_source_file1)
        self.binary_filename0 = os.path.realpath(binary_filename0)
        self.binary_filename1 = os.path.realpath(binary_filename1)
        self.revision = revision
        self.config_filename = os.path.realpath(config_filename)
        self.config = config_parser
        self.compiler = os.path.realpath(compiler)

        #Remove the bin extension of the firmware output filename
        if os.path.splitext(self.binary_filename0)[1]!='.bin':
            logging.error('Invalid binary output filename on file 0. It should have the .bin extension.')
            raise RuntimeError('Invalid binary output filename on file 0. It should have the .bin extension.')

        if os.path.splitext(self.binary_filename1)[1]!='.bin':
            logging.error('Invalid binary output filename on file 1. It should have the .bin extension.')
            raise RuntimeError('Invalid binary output filenameon file 1. It should have the .bin extension.')

        self.binary_filename_compiler0 = os.path.splitext(self.binary_filename0)[0]
        self.binary_filename_compiler1 = os.path.splitext(self.binary_filename1)[0]

        if not os.path.exists(self.compiler):
            logging.error('PASM compiler not found. Go to the firmware directory and issue the `make` command.')
            raise RuntimeError('PASM compiler not found.')

    ''' Returns True if the firmware needs recompilation '''
    def is_needing_firmware_compilation(self):
        config_mtime  = os.path.getmtime(self.config_filename) #modif time of config file

        if os.path.exists(self.binary_filename0):
            #Check if we need to rebuild the firmware
            fw_mtime      = os.path.getmtime(self.binary_filename0) #modif time of firmware file
            fw_src_mtime  = os.path.getmtime(self.firmware_source_file0) #modif time of firmware source file
            if fw_mtime  >= config_mtime and fw_mtime>=fw_src_mtime: #already up to date
                return False

        if os.path.exists(self.binary_filename1):
            #Check if we need to rebuild the firmware
            fw_mtime      = os.path.getmtime(self.binary_filename1) #modif time of firmware file
            fw_src_mtime  = os.path.getmtime(self.firmware_source_file1) #modif time of firmware source file
            if fw_mtime  >= config_mtime and fw_mtime>=fw_src_mtime: #already up to date
                return False

        return True

    def produce_firmware(self):
        if not self.is_needing_firmware_compilation():
            return True

        # Revision define
        revision = "-DREV_A3" if self.revision == "A3" else "-DREV_A4"
        
        cmd0 = [self.compiler,'-b', revision]
        cmd1 = [self.compiler,'-b', revision]

        # Define direction
        for s in ['x','y','z','e','h']:
            cmd0.append('-DSTEPPER_'+s.upper()+'_DIRECTION='+("0" if self.config.getint('Steppers', 'direction_'+s)>0 else "1"))

        # Construct the inversion mask
        inversion_mask = "-DINVERSION_MASK=0b00"
        for axis in ["X1", "X2", "Y1", "Y2", "Z1", "Z2"]:
            inversion_mask += "1" if self.config.getboolean('Endstops', 'invert_'+axis) else "0"

        cmd1.append(inversion_mask)

        # Construct the endstop lookup table. 
        for axis in ["X1", "X2", "Y1", "Y2", "Z1", "Z2"]:
            cmd1.append("-DSTEPPER_MASK_"+axis+"="+self.config.get('Endstops', 'lookup_mask_'+axis))

        cmd0.extend([self.firmware_source_file0, self.binary_filename_compiler0])
        cmd1.extend([self.firmware_source_file1, self.binary_filename_compiler1])

        logging.debug("Compiling firmware 0 with "+' '.join(cmd0))
        try:
            subprocess.check_output(cmd0, stderr=subprocess.STDOUT)
            logging.debug("Compilation succeeded.")
        except subprocess.CalledProcessError as e:
            logging.exception('Error while compiling firmware: ')
            logging.error('Command output:'+e.output)
            return False

        logging.debug("Compiling firmware 1 with "+' '.join(cmd1))
        try:
            subprocess.check_output(cmd1, stderr=subprocess.STDOUT)
            logging.debug("Compilation succeeded.")
        except subprocess.CalledProcessError as e:
            logging.exception('Error while compiling firmware: ')
            logging.error('Command output:'+e.output)
            return False

        return True

    ''' Return the path to the firmware bin file, None if the firmware cannot be produced. '''
    def get_firmware(self, prunum = 0):
        if prunum == 0:
            if not os.path.exists(self.binary_filename0) or self.is_needing_firmware_compilation():
                if not self.produce_firmware():
                    return None
            return self.binary_filename0
        else:
            if not os.path.exists(self.binary_filename1) or self.is_needing_firmware_compilation():
                if not self.produce_firmware():
                    return None
            return self.binary_filename1
    
