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
from six import iteritems

class PruFirmware:
    def __init__(self, firmware_source_file0, binary_filename0,
                 firmware_source_file1, binary_filename1,
                 printer, compiler, assembler, linker_cmdfile, repackage_cmdfile):
        """Create and initialize a PruFirmware

        Parameters
        ----------

        firmware_source_file : string
            The path to the firmware source to use to produce the firmware
        binary_filename : string
            Full path to the file where to store the final firmware file
            without the extension (without .bin)
        config_parser : ConfigParser
            The config parser with the config file already loaded
        compiler : string
            Path to the PRU C compiler
        assembler : string
            Path to the pasm assembler
        linker_cmdfile : string
            Path to the cmd file that maps the device for the linker
        repackage_cmdfile : string
            Path to the cmd file describing how to repackage the firmware
        """

        self.firmware_source_file0 = os.path.realpath(firmware_source_file0)
        self.firmware_source_file1 = os.path.realpath(firmware_source_file1)
        self.binary_filename0 = os.path.realpath(binary_filename0)
        self.binary_filename1 = os.path.realpath(binary_filename1)
        self.config = printer.config
        self.printer = printer
        self.compiler = os.path.realpath(compiler)
        self.assembler = os.path.realpath(assembler)
        self.linker_cmdfile = os.path.realpath(linker_cmdfile)
        self.repackage_cmdfile = os.path.realpath(repackage_cmdfile)

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

        if not os.path.exists(self.compiler):
            logging.error('CLPRU compiler not found.')
            raise RuntimeError('CLPRU compiler not found.')

        if not os.path.exists(self.assembler):
            logging.error('PASM assembler not found.')
            raise RuntimeError('PASM assembler not found.')

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

        config_file = self.make_config_file()

        # Copy the files to tmp, cos the pasm is really picky!
        tmp_name_0 = "/tmp/"+os.path.basename(self.firmware_source_file0)
        tmp_name_1 = "/tmp/"+os.path.basename(self.firmware_source_file1)
        tmp_output_name_0 = "/tmp/"+os.path.basename(self.binary_filename0)
        tmp_output_name_1 = "/tmp/"+os.path.basename(self.binary_filename1)

        logging.debug('Copying firmware 0 from ' + self.firmware_source_file0 + ' to ' + tmp_name_0)
        shutil.copyfile(self.firmware_source_file0, tmp_name_0)

        logging.debug('Copying firmware 1 from ' + self.firmware_source_file1 + ' to ' + tmp_name_1)
        shutil.copyfile(self.firmware_source_file1, tmp_name_1)

        return_value = self.build_firmware(tmp_name_0, tmp_output_name_0)

        if return_value == False:
            return False

        return_value = self.build_firmware(tmp_name_1, tmp_output_name_1)

        if return_value == False:
            return False

        shutil.copyfile(tmp_output_name_0, self.binary_filename0)
        shutil.copyfile(tmp_output_name_1, self.binary_filename1)

        return True

    def build_firmware(self, input, output):
        extension = os.path.splitext(input)[1]
        if extension == ".p":
            return self.build_firmware_assembled(input, output)
        elif extension == ".c":
            return self.build_firmware_compiled(input, output)
        else:
            raise RuntimeError("Unknown firmware extension: "+extension)

    def build_firmware_assembled(self, input, output):
        cmd = [self.assembler, '-b', input, os.path.splitext(output)[0]]
        logging.debug("Assembling firmware with " + ' '.join(cmd))
        try:
            subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            logging.debug("Compilation succeeded.")
        except subprocess.CalledProcessError as e:
            logging.exception('Error while compiling firmware: ')
            logging.error('Command output:' + e.output)
            return False
        return True

    def build_firmware_compiled(self, input, output):
        obj_output = os.path.splitext(output)[0] + ".obj"
        elf_output = os.path.splitext(output)[0] + ".elf"

        compile_cmd = [self.compiler, '-v3', '-O3', '--hardware_mac=on', '--endian=little', '-I/usr/src/pru-software-support-package/include/am335x',
                   '-I/usr/share/ti/cgt-pru/include', '--obj_directory', '/tmp', input]

        logging.debug("Compiling firmware with " + ' '.join(compile_cmd))
        try:
            subprocess.check_output(compile_cmd, stderr=subprocess.STDOUT)
            logging.debug("Compilation succeeded.")
        except subprocess.CalledProcessError as e:
            logging.exception('Error while compiling firmware: ')
            logging.error('Command output:' + e.output)
            return False

        link_cmd = [self.compiler, '-v3', '-O3', '--hardware_mac=on', '--endian=little', '-z', '-i', '/usr/share/ti/cgt-pru/lib',
                '--stack_size=0x100', '--heap_size=0x100', '--rom_model', '-o', elf_output, obj_output, self.linker_cmdfile]

        logging.debug("Linking firmware with " + ' '.join(link_cmd))
        try:
            subprocess.check_output(link_cmd, stderr=subprocess.STDOUT)
            logging.debug("Linking succeeded.")
        except subprocess.CalledProcessError as e:
            logging.exception('Error while linking firmware: ')
            logging.error('Command output:' + e.output)
            return False

        repackage_cmd = ['/usr/bin/hexpru', '-o', output, self.repackage_cmdfile, elf_output]

        logging.debug("Repacking firmware with " + ' '.join(repackage_cmd))
        try:
            subprocess.check_output(repackage_cmd, stderr=subprocess.STDOUT)
            logging.debug("Repacking succeeded.")
        except subprocess.CalledProcessError as e:
            logging.exception('Error while repacking firmware: ')
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

    def make_config_file(self):

        # Create a config file
        configFile_0 = os.path.join("/tmp", 'config.h')

        with open(configFile_0, 'w') as configFile:

            # GPIO banks
            banks      = {"0": 0, "1": 0, "2": 0, "3": 0}
            step_banks = {"0": 0, "1": 0, "2": 0, "3": 0}
            dir_banks  = {"0": 0, "1": 0, "2": 0, "3": 0}
            direction_mask = 0

            # Define step and dir pins
            for name, stepper in iteritems(self.printer.steppers):
                step_pin  = str(stepper.get_step_pin())
                step_bank = str(stepper.get_step_bank())
                dir_pin   = str(stepper.get_dir_pin())
                dir_bank  = str(stepper.get_dir_bank())
                configFile.write('#define STEPPER_' + name + '_STEP_BANK\t\t' + "STEPPER_GPIO_"+step_bank+'\n')
                configFile.write('#define STEPPER_' + name + '_STEP_PIN\t\t'  + step_pin+'\n')
                configFile.write('#define STEPPER_' + name + '_DIR_BANK\t\t'  + "STEPPER_GPIO_"+dir_bank+'\n')
                configFile.write('#define STEPPER_' + name + '_DIR_PIN\t\t'   + dir_pin+'\n')

                # Define direction
                direction = "0" if self.config.getint('Steppers', 'direction_' + name) > 0 else "1"
                configFile.write('#define STEPPER_'+ name +'_DIRECTION\t\t'+ direction +'\n')

                index = Printer.axis_to_index(name)
                direction_mask |= (int(direction) << index)

                # Generate the GPIO bank masks
                banks[step_bank]      |=  (1<<int(step_pin))
                banks[dir_bank]       |=  (1<<int(dir_pin))
                step_banks[step_bank] |=  (1<<int(step_pin))
                dir_banks[dir_bank]   |=  (1<<int(dir_pin))

            configFile.write('#define DIRECTION_MASK '+bin(direction_mask)+'\n')
            configFile.write('\n')

            # Define end stop pins and banks
            for name, endstop in iteritems(self.printer.end_stops):
                bank, pin = endstop.get_gpio_bank_and_pin()
                configFile.write('#define STEPPER_'+ name +'_END_PIN\t\t'+ str(pin) +'\n')
                configFile.write('#define STEPPER_'+ name +'_END_BANK\t\t'+ "GPIO_"+str(bank) +'_IN\n')

            configFile.write('\n')

            # Construct the end stop inversion mask
            inversion_mask = "#define INVERSION_MASK\t\t0b00"
            for name in ["Z2", "Y2", "X2", "Z1", "Y1", "X1"]:
                inversion_mask += "1" if self.config.getboolean('Endstops', 'invert_' + name) else "0"

            configFile.write(inversion_mask + "\n");

            # Construct the endstop lookup table.
            for name, endstop in iteritems(self.printer.end_stops):
                mask = 0

                # stepper name is x_cw or x_ccw
                option = 'end_stop_' + name + '_stops'
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

                logging.debug("Endstop {0} mask = {1}".format(name, bin(mask)))

                bin_mask = "0b"+(bin(mask)[2:]).zfill(16)
                configFile.write("#define STEPPER_MASK_" + name + "\t\t" + bin_mask + "\n")

            configFile.write("\n");


            # Put each dir and step pin in the proper buck if they are for GPIO0 or GPIO1 bank.
            # This is a restriction due to the limited capabilities of the pasm preprocessor.
            for name, bank in iteritems(banks):
                #bank = (~bank & 0xFFFFFFFF)
                configFile.write("#define GPIO"+name+"_MASK\t\t" +bin(bank)+ "\n");
            # for name, bank in iteritems(step_banks):
                #bank = (~bank & 0xFFFFFFFF)
            #    configFile.write("#define GPIO"+name+"_STEP_MASK\t\t" +bin(bank)+ "\n");
            for name, bank in iteritems(dir_banks):
                #bank = (~bank & 0xFFFFFFFF)
                configFile.write("#define GPIO"+name+"_DIR_MASK\t\t" +bin(bank)+ "\n");

            configFile.write("\n");

            # Add end stop delay to the config file
            end_stop_delay = self.config.getint('Endstops', 'end_stop_delay_cycles')
            configFile.write("#define END_STOP_DELAY " +str(end_stop_delay)+ "\n");
            
            revision = self.printer.config.replicape_revision.strip('0');
            
            # Note that these are all cycle counts of the 200MHz PRU - 1 cycle is 5ns
            if revision.startswith('A'): # DRV8825
                configFile.write("#define DELAY_BETWEEN_DIR_AND_STEP 130\n") # t_SU in the spec sheet
                configFile.write("#define DELAY_BETWEEN_STEP_AND_CLEAR 380\n") # t_WH in the spec sheet
                configFile.write("#define MINIMUM_DELAY_AFTER_STEP 380\n") # t_WL in the spec sheet
            elif revision.startswith('B'): # TMC2100
                configFile.write("#define DELAY_BETWEEN_DIR_AND_STEP 4\n") # t_DSU in the spec sheet
                configFile.write("#define DELAY_BETWEEN_STEP_AND_CLEAR 20\n") # t_SH in the spec sheet - assume internal clock of 14MHz, which means we need max(~85, t_clk+20). t_clk+20 is ~91.43, which we round up for safety
                configFile.write("#define MINIMUM_DELAY_AFTER_STEP 24\n") # t_SL with t_DSH added for safety
            else:
                raise RuntimeError("Unknown Replicape revision "+revision+", cannot determine stepper delays")
        return configFile_0

if __name__ == '__main__':
    from Printer import Printer
    from EndStop import EndStop
    from Stepper import Stepper, Stepper_00A3, Stepper_00A4, Stepper_00B1, Stepper_00B2, Stepper_00B3
    from CascadingConfigParser import CascadingConfigParser
    printer = Printer()


    # Parse the config files.
    printer.config = CascadingConfigParser(
        ['/etc/redeem/default.cfg'])

    # Init the 5 Stepper motors (step, dir, fault, DAC channel, name)
    printer.steppers["X"] = Stepper("GPIO0_27", "GPIO1_29", "GPIO2_4" , 0, 0, "X")
    printer.steppers["Y"] = Stepper("GPIO1_12", "GPIO0_22", "GPIO2_5" , 1, 1, "Y")
    printer.steppers["Z"] = Stepper("GPIO0_23", "GPIO0_26", "GPIO0_15", 2, 2, "Z")
    printer.steppers["E"] = Stepper("GPIO1_28", "GPIO1_15", "GPIO2_1" , 3, 3, "E")
    printer.steppers["H"] = Stepper("GPIO1_13", "GPIO1_14", "GPIO2_3" , 4, 4, "H")
    printer.steppers["A"] = Stepper("GPIO2_2" , "GPIO1_18", "GPIO0_14", 5, 5, "A")
    printer.steppers["B"] = Stepper("GPIO1_16", "GPIO0_5" , "GPIO0_14", 6, 6, "B")
    printer.steppers["C"] = Stepper("GPIO0_3" , "GPIO3_19", "GPIO0_14", 7, 7, "C")

    for es in ["X1", "X2", "Y1", "Y2", "Z1", "Z2"]:
        pin     = printer.config.get("Endstops", "pin_"+es)
        keycode = printer.config.getint("Endstops", "keycode_"+es)
        invert  = printer.config.getboolean("Endstops", "invert_"+es)
        printer.end_stops[es] = EndStop(pin, keycode, es, invert)


    pasm = "/home/elias/workspace/am335x_pru_package/pru_sw/utils/pasm"
    pru = PruFirmware("0.p", "0.bin", "1.p", "1.bin", printer, "")
    pru.make_config_file()
