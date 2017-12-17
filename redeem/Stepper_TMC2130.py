#!/usr/bin/env python
"""
A Stepper Motor Driver class for TMC2130

Author: Elias Bakken
email: elias(at)iagent(dot)no
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




import time
import logging
from Stepper import Stepper
from Printer import Printer
from threading import Thread
from Alarm import Alarm
from Key_pin import Key_pin

class TMC2130(Stepper):
    GCONF       = 0x00
    GSTAT       = 0x01
    IOIN        = 0x04
    IHOLD_IRUN  = 0x10
    TPOWERDOWN  = 0x11
    TSTEP       = 0x12
    TPWMTHRS    = 0x13
    TCOOLTHRS   = 0x14
    THIGH       = 0x15
    XDIRECT     = 0x2D
    VDCMIN      = 0x33
    MSLUT_0     = 0x60
    MSLUT_1     = 0x61
    MSLUT_2     = 0x62
    MSLUT_3     = 0x63
    MSLUT_4     = 0x64
    MSLUT_5     = 0x65
    MSLUT_6     = 0x66
    MSLUT_7     = 0x67
    MSLUTSEL    = 0x68
    MSLUTSTART  = 0x69
    MSCNT       = 0x6A
    MSCURACT    = 0x6B
    CHOPCONF    = 0x6C
    COOLCONF    = 0x6D
    DCCTRL      = 0x6E
    DRV_STATUS  = 0x6F
    PWMCONF     = 0x70
    PWM_SCALE   = 0x71
    ENCM_CTRL   = 0x72 
    LOST_STEPS  = 0x73

    SANITY_TEST_UNDONE = 0
    SANITY_TEST_PASSED = 1
    SANITY_TEST_FAILED_MAGIC = 2
    SANITY_TEST_FAILED_IOIN = 3

    def __init__(self, stepPin, dirPin, faultPin, name, spi):
        Stepper.__init__(self, stepPin, dirPin, faultPin, None, -1, name)
        logging.debug("Adding stepper with step {}, dir {}".format(stepPin, dirPin))

        self.current_enabled = False
        self.sanity_test = TMC2130.SANITY_TEST_UNDONE
        self.spi = spi
        self.regs = { # Addr, value pairs
            TMC2130.GCONF: 0, 
            TMC2130.GSTAT: 0,
            TMC2130.IOIN:  0, 
            TMC2130.IHOLD_IRUN: 0, 
            TMC2130.TPOWERDOWN: 0,
            TMC2130.TSTEP: 0, 
            TMC2130.TPWMTHRS: 0, 
            TMC2130.TCOOLTHRS: 0, 
            TMC2130.THIGH: 0, 
            TMC2130.XDIRECT: 0, 
            TMC2130.VDCMIN: 0, 
            TMC2130.MSLUT_0: 0,
            TMC2130.MSLUT_1: 0, 
            TMC2130.MSLUT_2: 0, 
            TMC2130.MSLUT_3: 0, 
            TMC2130.MSLUT_4: 0, 
            TMC2130.MSLUT_5: 0, 
            TMC2130.MSLUT_6: 0, 
            TMC2130.MSLUT_7: 0, 
            TMC2130.MSLUTSEL: 0, 
            TMC2130.MSLUTSTART: 0, 
            TMC2130.MSCNT: 0, 
            TMC2130.MSCURACT: 0, 
            TMC2130.CHOPCONF: 0, 
            TMC2130.COOLCONF: 0, 
            TMC2130.DCCTRL: 0, 
            TMC2130.DRV_STATUS: 0, 
            TMC2130.PWMCONF: 0, 
            TMC2130.PWM_SCALE: 0, 
            TMC2130.ENCM_CTRL: 0, 
            TMC2130.LOST_STEPS: 0
        }

        self.I_scale_analog = 0
        self.internal_Rsense= 0
        self.en_pwm_mode    = 1
        self.shaft          = 0
        self.diag0_error    = 1
        self.diag0_otpw     = 1
        self.diag0_stall    = 1 # These seem inverted from the datasheet
        self.diag1_stall    = 1 # These seem inverted from the datasheet
        self.direct_mode    = 0
        self.stop_enable    = 0

        self.diss2g   = 1 # Short to ground protection 
        self.dedge    = 0 # Enable double edge step pulses
        self.intpol   = 1 # Interpolate to 256 microstepping
        self.mres     = 3 # Micro step resolution
        self.sync     = 0 # PWM sync clock
        self.vhighchm = 0 # High velocity chopper mode
        self.vhighfs  = 0 # High velocity full step selection 
        self.vsense   = 1 # voltage sensitivity
        self.tbl      = 2 # TBL blank time
        self.chm      = 0 # Chopper mode
        self.rndtf    = 0 # Random TOFF time
        self.disfdcc  = 0 # Fast decay mode
        self.fd3      = 0 # TFD[3]
        self.hend     = 0 # hysteresis low value OFFSET sine wave offset
        self.hstrt    = 0 # hysteresis start value added to HEND
        self.toff     = 5 # TOFF off time

        self.sfilt    = 0 # Enables the stallGuard2 filter
        self.sgt      = 0x0F # stallGuard2 threshold value
        self.seimin   = 0 # minimum current for smart current control
        self.sedn     = 0 # current down step speed
        self.semax    = 2 # stallGuard2 hysteresis value for smart current control
        self.seup     = 0 # current up step width
        self.semin    = 1 # minimum stallGuard2 value for smart current

        self.ihold    = 3 # Hold current 
        self.irun     = 8 # Run current
        self.ihold_delay = 10 # Delay before going to hold current

        self.thigh = 0#(1<<18)

    def update(self):
        self.run_sanity_test()
        if self.sanity_test != TMC2130.SANITY_TEST_PASSED:
            logging.warning("Sanity test failed for {}: {}, {}".format(self.name, self.sanity_test, hex(self.regs[TMC2130.XDIRECT])))
        self.read_gstat()
        self.update_gconf()
        self.update_chopconf()
        self.update_coolconf()
        self.set_hold_current()
        self.update_thigh()
        
    # High level functions
    def set_current_enabled(self):
        self.set_enabled()

    def set_current_disabled(self):
        self.set_disabled()

    def get_diagnostics(self, update=True):
        self.get_drv_status()
        logging.debug("Stepper {} diagnostics:\n----------------------".format(self.name))
        if self.stst:
             logging.debug("standstill indicator")
        if self.olb: 
             logging.debug("open load indicator phase B")
        if self.ola: 
             logging.debug("open load indicator phase A")
        if self.s2gb: 
             logging.debug("short to ground indicator phase B")
        if self.s2ga:
             logging.debug("short to ground indicator phase A")
        if self.otpw:
             logging.debug("overtemperature pre-warning flag")
        if self.ot:
             logging.debug("overtemperature flag")
        if self.stallguard:
             logging.debug("stallGuard2 status")
        if self.fsactive:
             logging.debug("full step active")
        logging.debug("actual motor current: "+str(self.cs_actual))
        logging.debug("stallGuard2 result: "+str(self.sg_result))

    # Update the status from the SPI transfer
    def update_status(self, stat):
        self.reset_flag   = bool(stat & (1<<0))
        self.driver_error = bool(stat & (1<<1))
        self.stall_guard  = bool(stat & (1<<2))
        self.standstill   = bool(stat & (1<<3))

    def update_gconf(self, update=True):
        val  = (self.I_scale_analog<<0)
        val |= (self.internal_Rsense<<1)
        val |= (self.en_pwm_mode<<2)
        val |= (self.shaft<<4)
        val |= (self.diag0_error<<5)
        val |= (self.diag0_otpw<<6)
        val |= (self.diag0_stall<<7)
        val |= (self.diag1_stall<<8)
        val |= (self.stop_enable<<15)
        val |= (self.direct_mode<<16)

        self.regs[TMC2130.GCONF] = val
        if update:
            #logging.debug("GCONF: "+bin(self.regs[TMC2130.GCONF]))
            self.write(TMC2130.GCONF)
            #self.read(TMC2130.GCONF)
            #logging.debug("GCONF: "+bin(self.regs[TMC2130.GCONF]))

    def update_chopconf(self, update=True):
        val  = (self.diss2g << 30)
        val |= (self.dedge << 29)
        val |= (self.intpol << 28)
        val |= (self.mres << 24)
        val |= (self.sync << 20)
        val |= (self.vhighchm<<19)
        val |= (self.vhighfs<<18)
        val |= (self.vsense<<17)
        val |= (self.tbl<<15)
        val |= (self.chm<<14)
        val |= (self.rndtf<<13)
        val |= (self.disfdcc<<12)
        val |= (self.fd3<<11)
        val |= (self.hend<<7)
        val |= (self.hstrt<<4)
        val |= (self.toff<<0)


        self.regs[TMC2130.CHOPCONF] = val
        #self.regs[TMC2130.CHOPCONF] = 3 | (1<<28)
        if update:
            #logging.debug("CHOPCONF: "+hex(self.regs[TMC2130.CHOPCONF]))
            self.write(TMC2130.CHOPCONF)
            #self.read(TMC2130.CHOPCONF)
            #logging.debug("CHOPCONF: "+hex(self.regs[TMC2130.CHOPCONF]))

    def update_coolconf(self, update=True):        
        val  = (self.semin<<0)
        val |= (self.seup<<5)
        val |= (self.semax<<8)
        val |= (self.sedn<<13)
        val |= (self.seimin<<15)
        val |= (self.sgt<<16)
        val |= (self.sfilt<<24)

        self.regs[TMC2130.COOLCONF] = val
        if update:
            self.write(TMC2130.COOLCONF)

    def update_thigh(self, update=True):
        self.regs[TMC2130.THIGH] = self.thigh
        if update: 
            self.write(TMC2130.THIGH)

    def read_gstat(self, update=True):
        self.read(TMC2130.GSTAT)
        self.drv_reset   = bool(self.regs[TMC2130.GSTAT] & (1<0))
        self.drv_err = bool(self.regs[TMC2130.GSTAT] & (1<<1))
        self.uv_cp   = bool(self.regs[TMC2130.GSTAT] & (1<<2))

    def set_hold_current(self, update=True):
        val  = (self.ihold<<0)
        val |= (self.irun<<8)
        val |= (self.ihold_delay<<16)
            
        self.regs[TMC2130.IHOLD_IRUN] = val
        if update: 
            self.write(TMC2130.IHOLD_IRUN)
    
    def get_tstep(self):
        pass

    def get_pins(self):
        self.read(TMC2130.IOIN)
        return bin(self.regs[TMC2130.IOIN])

    def get_drv_status(self, update=True):
        self.read(TMC2130.DRV_STATUS)
        self.stst = bool(self.regs[TMC2130.DRV_STATUS] & (1<<31))
        self.olb  = bool(self.regs[TMC2130.DRV_STATUS] & (1<<30))
        self.ola  = bool(self.regs[TMC2130.DRV_STATUS] & (1<<29))
        self.s2gb = bool(self.regs[TMC2130.DRV_STATUS] & (1<<28))
        self.s2ga = bool(self.regs[TMC2130.DRV_STATUS] & (1<<27))
        self.otpw = bool(self.regs[TMC2130.DRV_STATUS] & (1<<26))
        self.ot   = bool(self.regs[TMC2130.DRV_STATUS] & (1<<25))
        self.stallguard = bool(self.regs[TMC2130.DRV_STATUS] & (1<<24))

        self.cs_actual = (self.regs[TMC2130.DRV_STATUS] & (0x1F<<16)>>16)
        self.fsactive  = bool(self.regs[TMC2130.DRV_STATUS] & (1<<15))
        self.sg_result = self.regs[TMC2130.DRV_STATUS] & (0x3F)

    def run_sanity_test(self):
        # Check that what we write to a register can be read back
        magic = 0x12345678
        self.regs[TMC2130.XDIRECT] = magic
        self.write(TMC2130.XDIRECT)
        self.read(TMC2130.XDIRECT)
        if self.regs[TMC2130.XDIRECT] != magic:
            self.sanity_test = TMC2130.SANITY_TEST_FAILED_MAGIC
            return
        # Reset to 0
        self.regs[TMC2130.XDIRECT] = 0x0
        self.write(TMC2130.XDIRECT)
        
        # TODO: Add test for high/low on step/dir pins
        self.read(TMC2130.IOIN)
        if (self.regs[TMC2130.IOIN] & 0xFF<<24)>>24 != 0x11:
            self.sanity_test = TMC2130.SANITY_TEST_FAILED_IOIN
            return
        self.sanity_test = TMC2130.SANITY_TEST_PASSED

    def get_capabilities(self):
        self.get_drv_status()
        ret = "Stepper {} diagnostics:\n".format(self.name)
        if self.stst:
             ret += " - standstill indicator\n"
        if self.olb: 
             ret += " - open load indicator phase B\n"
        if self.ola: 
             ret += " - open load indicator phase A\n"
        if self.s2gb: 
             ret += " - short to ground indicator phase B\n"
        if self.s2ga:
             ret += " - short to ground indicator phase A\n"
        if self.otpw:
             ret += " - overtemperature pre-warning flag\n"
        if self.ot:
             ret += " - overtemperature flag\n"
        if self.stallguard:
             ret += " - stallGuard2 status\n"
        if self.fsactive:
             ret += " - full step active\n"
        ret += "actual motor current: {}\n".format(self.cs_actual)
        ret += "stallGuard2 result: {}\n".format(self.sg_result)
        ret += "Tstep: {}\n".format(self.get_tstep())
        ret += "Pins: {}\n".format(self.get_pins())

        ret += "----------------------\n"
        return ret

    def set_microstepping(self, value, force_update=False):
        logging.debug("")       
        if value == 1:
            self.mres = 8
        elif value == 2:
            self.mres = 7
        elif value == 4:
            self.mres = 6
        elif value == 8:
            self.mres = 5
        elif value == 16:
            self.mres = 4
        elif value == 32:
            self.mres = 3
        elif value == 64:
            self.mres = 2
        elif value == 128:
            self.mres = 1
        elif value == 256:
            self.mres = 0
        else:
            logging.warning("Wrong microstepping value: '{}', using 16 (1/16th step) for {}".format(value, self.name))
            value = 16
            mres = 5
        self.update_chopconf()
        self.microsteps = value
        self.mmPrStep    = 1.0/(self.steps_pr_mm*self.microsteps)

        # update the Printer class with new values
        stepper_num = self.printer.axis_to_index(self.name)
        self.printer.steps_pr_meter[stepper_num] = self.get_steps_pr_meter()
        logging.debug("Updated stepper {} to 1/{}th step ".format(self.name, value))   
        self.microstepping = value

    def set_current_value(self, i_rms):
        """ Current chopping limit (This is the value you can change) """
        #TODO: Implement
        self.current_value = i_rms

    def set_disabled(self, update=True):
        self.toff = 0
        self.update_chopconf()

    def set_enabled(self, force_update=False):
        self.toff = 4
        self.update_chopconf()

    def set_decay(self, value):
        self.decay = value # For saving the setting with M500

    def reset(self):
        self.set_disabled()
        self.set_enabled()

    # Lower level stuff
    def get_index(self):
        return Stepper.printer.axis_to_index(self.name)

    def get_read_reg(self, addr):
        value = self.regs[addr]
        return [addr, int((value & (0xFF<<24))>>24), int((value & (0xFF<<16))>>16), int((value & (0xFF<<8))>>8), int((value & 0xFF))]

    def get_write_reg(self, addr):
        value = self.regs[addr]
        return [addr|0x80, int((value & (0xFF<<24))>>24), int((value & (0xFF<<16))>>16), int((value & (0xFF<<8))>>8), int((value & 0xFF))]
    
    def set_reg(self, addr, val):
        self.regs[addr] = val

    def write(self, addr):
        steppers = [s for s in Stepper.printer.steppers_ordered if s.spi == self.spi]
        steppers.reverse()
        to_send = [item for sublist in [s.get_write_reg(addr) for s in steppers] for item in sublist]
        status = self.spi.xfer(to_send)
        for index, stepper in enumerate(steppers):
            stepper.update_status(status[index*5])

    def read(self, addr):
        steppers = [s for s in Stepper.printer.steppers_ordered if s.spi == self.spi]
        steppers.reverse()
        to_send = [item for sublist in [s.get_read_reg(addr) for s in steppers] for item in sublist]
        # Twice, see the datasheet
        status = self.spi.xfer(to_send)
        status = self.spi.xfer(to_send)
        # Update status and reg
        for index, stepper in enumerate(steppers):
            stepper.update_status(status[index*5])
            regs = status[index*5+1:index*5+5]
            val = regs[3] | (regs[2]<<8) | (regs[1]<<16) | (regs[0]<<24)
            stepper.set_reg(addr, val)

# Simple test procedure for the steppers
if __name__ == '__main__':
    import spidev
    spi_0_0 = spidev.SpiDev()
    spi_0_0.open(0, 0)
    Stepper.printer = Printer()
    spi_1_0 = spidev.SpiDev()
    spi_1_0.open(1, 0)
    spi_1_1 = spidev.SpiDev()
    spi_1_1.open(1, 1)
    

    with open("/sys/class/gpio/gpio18/value", "w") as f:
        f.write("1\n")
    
    Stepper.printer.add_stepper(TMC2130("GPIO3_14", "GPIO3_15", "GPIO0_27", "X", spi_0_0))
    Stepper.printer.add_stepper(TMC2130("GPIO3_16", "GPIO3_17", "GPIO2_0",  "Y", spi_0_0))
    Stepper.printer.add_stepper(TMC2130("GPIO3_18", "GPIO3_19", "GPIO1_16", "Z", spi_0_0))
    Stepper.printer.add_stepper(TMC2130("GPIO3_20", "GPIO3_21", "GPIO2_1",  "E", spi_0_0))
    Stepper.printer.add_stepper(TMC2130("GPIO2_26", "GPIO2_27", "GPIO0_29", "H", spi_0_0))
    Stepper.printer.add_stepper(TMC2130("GPIO2_28", "GPIO2_29", "GPIO0_26", "A", spi_0_0))
    Stepper.printer.add_stepper(TMC2130("GPIO2_30", "GPIO2_31", None, "B", spi_1_0))
    Stepper.printer.add_stepper(TMC2130("GPIO1_12", "GPIO1_13", None, "C", spi_1_1))

    for i in Stepper.printer.steppers:
        s = Stepper.printer.steppers[i]
        s.update()
        print("Step pin: "+str(s.name)+" "+str(s.get_step_pin()))
        print("Dir pin: "+str(s.name)+" "+str(s.get_dir_pin()))

    with open("/sys/class/gpio/gpio18/value", "w") as f:
        f.write("0\n")


