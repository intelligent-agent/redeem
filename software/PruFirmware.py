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
import shutil

class PruFirmware:

    def __init__(self, firmware_source_file0, binary_filename0, firmware_source_file1, binary_filename1, revision, config_filename, config_parser,compiler):
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

        ret0 = True
        ret1 = True

        if os.path.exists(self.binary_filename0):
            #Check if we need to rebuild the firmware
            fw_mtime      = os.path.getmtime(self.binary_filename0) #modif time of firmware file
            fw_src_mtime  = os.path.getmtime(self.firmware_source_file0) #modif time of firmware source file
            if fw_mtime  >= config_mtime and fw_mtime>=fw_src_mtime: #already up to date
                ret0 = False

        if os.path.exists(self.binary_filename1):
            #Check if we need to rebuild the firmware
            fw_mtime      = os.path.getmtime(self.binary_filename1) #modif time of firmware file
            fw_src_mtime  = os.path.getmtime(self.firmware_source_file1) #modif time of firmware source file
            if fw_mtime  >= config_mtime and fw_mtime>=fw_src_mtime: #already up to date
                ret1 = False


        return ret0 or ret1

    def produce_firmware(self):
        if not self.is_needing_firmware_compilation():
            return True

        # Create a config file
        configFile_0 = os.path.join(os.path.dirname(self.firmware_source_file0) ,'config.h')



        with open(configFile_0, 'w') as configFile:
            configFile.write("#define REV_A3\n" if self.revision == "A3" else "#define REV_A4\n")

            # Define direction
            for s in ['x','y','z','e','h']:
                configFile.write('#define STEPPER_'+s.upper()+'_DIRECTION\t\t'+("0" if self.config.getint('Steppers', 'direction_'+s)>0 else "1")+'\n')

            # #Add endstop config

            # #Min X
            # (pin,bank) = self.end_stops["X1"].get_gpio_bank_and_pin()
            # cmd.extend(['#define STEPPER_X_END_MIN_PIN\t\t'+str(pin),'#define STEPPER_X_END_MIN_BANK\t\tGPIO_'+str(bank)+'_IN']);

            # #Min Y
            # (pin,bank) = self.end_stops["Y1"].get_gpio_bank_and_pin()
            # cmd.extend(['#define STEPPER_Y_END_MIN_PIN\t\t'+str(pin),'#define STEPPER_Y_END_MIN_BANK\t\tGPIO_'+str(bank)+'_IN']);

            # #Min Z
            # (pin,bank) = self.end_stops["Z1"].get_gpio_bank_and_pin()
            # cmd.extend(['#define STEPPER_X_END_MIN_PIN\t\t'+str(pin),'#define STEPPER_Z_END_MIN_BANK\t\tGPIO_'+str(bank)+'_IN']);

            # #Max X
            # (pin,bank) = self.end_stops["X2"].get_gpio_bank_and_pin()
            # cmd.extend(['#define STEPPER_X_END_MAX_PIN\t\t'+str(pin),'#define STEPPER_X_END_MAX_BANK\t\tGPIO_'+str(bank)+'_IN']);

            # #Max Y
            # (pin,bank) = self.end_stops["Y2"].get_gpio_bank_and_pin()
            # cmd.extend(['#define STEPPER_Y_END_MAX_PIN\t\t'+str(pin),'#define STEPPER_Y_END_MAX_BANK\t\tGPIO_'+str(bank)+'_IN']);

            # #Max Z
            # (pin,bank) = self.end_stops["Z2"].get_gpio_bank_and_pin()
            # cmd.extend(['#define STEPPER_X_END_MAX_PIN\t\t'+str(pin),'#define STEPPER_Z_END_MAX_BANK\t\tGPIO_'+str(bank)+'_IN']);

            # Construct the inversion mask
            inversion_mask = "#define INVERSION_MASK\t\t0b00"
            for axis in ["X1", "X2", "Y1", "Y2", "Z1", "Z2"]:
                inversion_mask += "1" if self.config.getboolean('Endstops', 'invert_'+axis) else "0"

            configFile.write(inversion_mask+"\n");

            # Construct the endstop lookup table. 
            for axis in ["X1", "X2", "Y1", "Y2", "Z1", "Z2"]:
                configFile.write("#define STEPPER_MASK_"+axis+"\t\t"+self.config.get('Endstops', 'lookup_mask_'+axis)+"\n")

        configFile_1 = os.path.join(os.path.dirname(self.firmware_source_file1) ,'config.h')

        if os.path.dirname(self.firmware_source_file0)!=os.path.dirname(self.firmware_source_file0):
            shutil.copyfile(configFile_0,configFile_1)

        cmd0 = [self.compiler,'-b','-DHAS_CONFIG_H']
        cmd1 = [self.compiler,'-b','-DHAS_CONFIG_H']

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
        if self.is_needing_firmware_compilation():
            if not self.produce_firmware():
                return None

        if prunum == 0:
            return self.binary_filename0
        else:
            return self.binary_filename1
    
