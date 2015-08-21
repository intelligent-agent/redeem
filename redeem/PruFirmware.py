"""
PruFirmware.py file for Replicape.

Handles the compilation of the PRU firmware based on the different printer settings on the fly.

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
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

import os
import logging
import subprocess
import shutil
import re


class PruFirmware:
    def __init__(self, firmware_source_file0, binary_filename0,
                 firmware_source_file1, binary_filename1, revision,
                 config_parser, compiler):
        """Create and initialize a PruFirmware

        Parameters
        ----------

        firmware_source_file : string
            The path to the firmware source to use to produce the firmware
        binary_filename : string
            Full path to the file where to store the final firmware file
            without the extension (without .bin)
        revision : string
            The revision of the board (00A3 or 00A4)
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
        self.config = config_parser
        self.compiler = os.path.realpath(compiler)

        #Remove the bin extension of the firmware output filename
        if os.path.splitext(self.binary_filename0)[1] != '.bin':
            logging.error(
                'Invalid binary output filename on file 0. '
                'It should have the .bin extension.')
            raise RuntimeError(
                'Invalid binary output filename on file 0. '
                'It should have the .bin extension.')

        if os.path.splitext(self.binary_filename1)[1] != '.bin':
            logging.error(
                'Invalid binary output filename on file 1. '
                'It should have the .bin extension.')
            raise RuntimeError(
                'Invalid binary output filenameon file 1. '
                'It should have the .bin extension.')

        self.binary_filename_compiler0 = \
            os.path.splitext(self.binary_filename0)[0]
        self.binary_filename_compiler1 = \
            os.path.splitext(self.binary_filename1)[0]

        if not os.path.exists(self.compiler):
            logging.error(
                'PASM compiler not found. '
                'Go to the firmware directory and issue the `make` command.')
            raise RuntimeError('PASM compiler not found.')

    def is_needing_firmware_compilation(self):
        """ Returns True if the firmware needs recompilation """
        config_mtime = self.config.timestamp()  # modif time of config file

        ret0 = True
        ret1 = True

        if os.path.exists(self.binary_filename0):
            # Check if we need to rebuild the firmware
            fw_mtime = os.path.getmtime(
                self.binary_filename0)  # modif time of firmware file
            fw_src_mtime = os.path.getmtime(
                self.firmware_source_file0)  # modif time of firmware source
            if fw_mtime >= config_mtime and fw_mtime >= fw_src_mtime:
                # already up to date
                ret0 = False

        if os.path.exists(self.binary_filename1):
            #Check if we need to rebuild the firmware
            fw_mtime = os.path.getmtime(
                self.binary_filename1)  # modif time of firmware file
            fw_src_mtime = os.path.getmtime(
                self.firmware_source_file1)  # modif time of firmware source
            if fw_mtime >= config_mtime and fw_mtime >= fw_src_mtime:
                # already up to date
                ret1 = False

        return ret0 or ret1

    def produce_firmware(self):
        if not self.is_needing_firmware_compilation():
            return True

        # Create a config file
        configFile_0 = os.path.join("/tmp", 'config.h')

        with open(configFile_0, 'w') as configFile:
            if self.revision in ["00A3"]:
                configFile.write("#define REV_A3\n")
            elif self.revision in ["00B2"]:
                configFile.write("#define REV_B2\n")
            else:
                configFile.write("#define REV_A4\n")

            # Define direction
            for s in ['x', 'y', 'z', 'e', 'h']:
                configFile.write(
                    '#define STEPPER_' + s.upper() + '_DIRECTION\t\t' + (
                        "0" if self.config.getint('Steppers',
                                                  'direction_' + s) > 0 else "1") + '\n')          
            # Construct the inversion mask
            inversion_mask = "#define INVERSION_MASK\t\t0b00"
            for axis in ["Z2", "Y2", "X2", "Z1", "Y1", "X1"]:
                inversion_mask += "1" if self.config.getboolean('Endstops',
                                                                'invert_' + axis) else "0"

            configFile.write(inversion_mask + "\n");

            # Construct the endstop lookup table.
            for axis in ["X1","Y1","Z1","X2","Y2","Z2"]:
                mask = 0
                # stepper name is x_cw or x_ccw
                option = 'end_stop_' + axis + '_stops'
                for stepper in self.config.get('Endstops', option).split(","):
                    stepper = stepper.strip()
                    if stepper == "":
                        continue
                    m = re.search('^([xyzehabc])_(ccw|cw|pos|neg)$', stepper)
                    if (m == None):
                        raise RuntimeError("'" + stepper + "' is invalid for " + option)

                    # direction should be 1 for normal operation and -1 to invert the stepper.
                    if (m.group(2) == "pos"):
                        direction = -1
                    elif (m.group(2) == "neg"):
                        direction = 1
                    else:
                        direction = 1 if self.config.getint('Steppers', 'direction_' + stepper[0]) > 0 else -1
                        if (m.group(2) == "ccw"): 
                            direction *= -1

                    cur = 1 << ("xyzehabc".index(m.group(1)))
                    if (direction == -1):
                        cur <<= 8
                    mask += cur
                bin_mask = "0b"+(bin(mask)[2:]).zfill(16)
                configFile.write("#define STEPPER_MASK_" + axis + "\t\t" + bin_mask + "\n")

        if self.revision in ["0A4A", "00A4"]:
            configFile_1 = os.path.join(
                os.path.dirname(self.firmware_source_file1), 'config_00A4.h')
        elif self.revision in ["00B1", "00B2"]:
            configFile_1 = os.path.join(
                os.path.dirname(self.firmware_source_file1), 'config_00B2.h')
        else:            
            configFile_1 = os.path.join(
                os.path.dirname(self.firmware_source_file1), 'config_00A3.h')

        cmd0 = [self.compiler, '-b', '-DHAS_CONFIG_H']
        cmd1 = [self.compiler, '-b', '-DHAS_CONFIG_H']

        # Copy the files to tmp, cos the pasm is really picky!
        tmp_name_0 = "/tmp/"+os.path.splitext(os.path.basename(self.firmware_source_file0))[0]
        tmp_name_1 = "/tmp/"+os.path.splitext(os.path.basename(self.firmware_source_file1))[0]
        shutil.copyfile(self.firmware_source_file0, tmp_name_0+".p")
        shutil.copyfile(self.firmware_source_file1, tmp_name_1+".p")

        # Copy the config file
        shutil.copyfile(configFile_1, "/tmp/"+os.path.basename(configFile_1))
        

        cmd0.extend([tmp_name_0+".p", tmp_name_0])
        cmd1.extend([tmp_name_1+".p", tmp_name_1])

        logging.debug("Compiling firmware 0 with " + ' '.join(cmd0))
        try:
            subprocess.check_output(cmd0, stderr=subprocess.STDOUT)
            # Move the file back
            shutil.copyfile(tmp_name_0+".bin", self.binary_filename_compiler0+".bin")
            logging.debug("Compilation succeeded.")
        except subprocess.CalledProcessError as e:
            logging.exception('Error while compiling firmware: ')
            logging.error('Command output:' + e.output)
            return False

        logging.debug("Compiling firmware 1 with " + ' '.join(cmd1))
        try:
            subprocess.check_output(cmd1, stderr=subprocess.STDOUT)
            # Move the file back
            shutil.copyfile(tmp_name_1+".bin", self.binary_filename_compiler1+".bin")
            logging.debug("Compilation succeeded.")
        except subprocess.CalledProcessError as e:
            logging.exception('Error while compiling firmware: ')
            logging.error('Command output:' + e.output)
            return False

        return True

    def get_firmware(self, prunum=0):
        """ Return the path to the firmware bin file, None if the firmware
        cannot be produced. """
        if self.is_needing_firmware_compilation():
            if not self.produce_firmware():
                return None

        if prunum == 0:
            return self.binary_filename0
        else:
            return self.binary_filename1
