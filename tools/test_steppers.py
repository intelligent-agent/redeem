#!/usr/bin/python 
# Measure voltage and current on input
from __future__ import print_function
import time
import spidev
spi = spidev.SpiDev()
spi.open(0, 0)
spi.mode = 3

def get_diag(byte):
    res = ""
    if(byte & (1<<0)):
        res += "reset_flag "
    if(byte & (1<<1)):
        res += "driver_error "
    if(byte & (1<<2)):
        res += "stall_guard "
    if(byte & (1<<3)):
        res += "standstill "
    return res

#Input voltage
def get_status(index):
    to_send = [0x00, 0x00, 0x00, 0x00, 0x00]*6
    regs = spi.xfer(to_send)
    to_send = [0x00, 0x00, 0x00, 0x00, 0x00]*6
    regs = spi.xfer(to_send)
    res = ""
    for i in range(6):
        byte = regs[i*5]
        res += str(i)+": "
        if(byte & (1<<0)):
            res += "rf "
        if(byte & (1<<1)):
            res += "de "
        if(byte & (1<<2)):
            res += "sg "
        if(byte & (1<<3)):
            res += "ss "
        res += ", "
    print(res+"\r", end="")

def update_status(regs):
    for i in range(6):
        res = get_diag(regs[i*5])
        #if res:
        #    print(res)

def write_regs(reg, value):
    to_send = [reg | 0x80, int((value & (0xFF<<24))>>24), int((value & (0xFF<<16))>>16), int((value & (0xFF<<8))>>8), int((value & 0xFF))]*6
    #print([hex(byte) for byte in to_send])
    res = spi.xfer2(to_send)
    #print([hex(byte) for byte in res])
    to_send = [0]*5*6
    res = spi.xfer2(to_send)
    #print([hex(byte) for byte in res])


def read_regs(reg):
    to_send = [reg, 0x00, 0x00, 0x00, 0x00]*6
    res = spi.xfer2(to_send)
    #update_status(res)
    to_send = [0x00, 0x00, 0x00, 0x00, 0x00]*6
    regs = spi.xfer2(to_send)
    #update_status(regs)
    #print(regs)
    r = [0]*6
    for i in range(6):
        r[i] = regs[(i*5)+4] | (regs[(i*5)+3]<<8) | (regs[(i*5)+2]<<16) | (regs[(i*5)+1]<<24)
    return r

def set_hold_current():
    ihold = 2
    irun = 4
    ihold_delay = 10
    reg = 0
    reg |= (ihold<<0)
    reg |= (irun<<8)
    reg |= (ihold_delay<<16)
    write_regs(0x10,  reg)
    
    
def set_chopconf(mres_in=3):
    diss2g   = 1 # Short to ground protection 
    dedge    = 0 # Enable double edge step pulses
    intpol   = 1 # Interpolate to 256 microstepping
    mres     = mres_in # Micro step resolution
    sync     = 0 # PWM sync clock
    vhighchm = 0 # High velocity chopper mode
    vhighfs  = 0 # High velocity full step selection 
    vsense   = 1 # voltage senseitivity
    tbl      = 2 # TBL blank time
    chm      = 0 # Chopper mode
    hend     = 0 # hysteresis low value OFFSET sine wave offset
    hstrt    = 4 # hysteresis start value added to HEND
    toff     = 4 # TOFF off time

    reg  = (diss2g << 30)
    reg |= (dedge << 29)
    reg |= (intpol << 28)
    reg |= (mres << 24)
    reg |= (sync << 20)
    reg |= (vhighchm<<19)
    reg |= (vhighfs<<18)
    reg |= (vsense<<17)
    reg |= (tbl<<15)
    reg |= (chm<<14)
    reg |= (hend<<7)
    reg |= (hstrt<<4)
    reg |= (toff<<0)

    write_regs(0x6C, reg)


def set_pwm_threshold():
    tpwmthrs = 1000
    tcoolthrs = 1000
    thigh = 1000
    write_regs(0x13, tpwmthrs)
    write_regs(0x14, tcoolthrs)
    write_regs(0x15, thigh)


def read_chopconf():
    i = 0
    for r in read_regs(0x6C):
        print("S: "+str(i))
        if r & (1<<30):
            print("diss2g")
        if r & (1<<29):
            print("dedge")
        if r & (1<<28):
            print("intpol")
        if r & (1<<17):
            print("vsense")
        if r & (3<<15):
            print("TBL: "+hex((3<<15)>>15))
        if r & (1<<14):
            print("chm")
        if r & (0xF):
            print("T_OFF: "+hex(r & 0xF))
        i += 1

def set_coolconf():
    sfilt = 0
    sgt = 0x0F
    seimin = 0
    sedn = 0
    semax = 2
    seup = 0
    semin  = 1
    
    reg = 0
    reg |= (semin<<0)
    reg |= (seup<<5)
    reg |= (semax<<8)
    reg |= (sedn<<13)
    reg |= (seimin<<15)
    reg |= (sgt<<16)
    reg |= (sfilt<<24)
    write_regs(0x6D, reg)
    

def get_drv_status():
    print("DRV_STATUS: ")
    regs = read_regs(0x6F)
    i = 0
    for r in regs:
        print("S: "+str(i))
        i += 1
        if r & (1<<31):
            print("standstill indicator")
        if r & (1<<30):
            print("open load indicator phase B")
        if r & (1<<29):
            print("open load indicator phase A")
        if r & (1<<28):
            print("short to ground indicator phase B")
        if r & (1<<27):
            print("short to ground indicator phase A")
        if r & (1<<26):
            print("overtemperature pre-warning flag")
        if r & (1<<25):
            print("overtemperature flag")
        if r & (1<<24):
            print("stallGuard2 status")
        if r & (1<<15):
            print("Full step active")

        print("actual motor current: "+str((r & (0x1F<<16))>>16))
        print("stallGuard2 result: "+str(r & (0x3FF)))
    print("")


def set_microstepping(value):
    if value == 1:
        write_regs(0x6C, (0xC0<<24)) # Fullstep


def set_gconf():
    I_scale_analog = 0
    internal_Rsense = 0
    en_pwm_mode = 0
    diag0_error = 1
    diag0_otpw  = 1
    diag0_stall = 1
    diag1_stall = 1
    direct_mode = 0
    stop_enable = 0

    reg = 0
    reg |= (I_scale_analog<<0)
    reg |= (internal_Rsense<<1)
    reg |= (en_pwm_mode<<2)
    reg |= (diag0_error<<5)
    reg |= (diag0_otpw<<6)
    reg |= (diag0_stall<<7)
    reg |= (diag1_stall<<8)
    reg |= (stop_enable<<15)
    reg |= (direct_mode<<16)
    write_regs(0x00, reg)
    

def get_tstep():
    return ["{0:#0{1}x}".format(reg, 6) for reg in read_regs(0x12)]

def passing_sanity_test():
    # Check that things are set up properly
    magic = 0xBABE7175
    write_regs(0x2D, magic)
    for reg in read_regs(0x2D):
        if reg != magic:
            return 1
    write_regs(0x2D, 0x00000000)

    for i, reg in enumerate(read_regs(0x04)):
        if ((reg & 0xff<<24)>>24) != 0x11:
            return 2
    
    
    return 0

def get_pins():
    return [bin(reg & 0xFF) for reg in read_regs(0x04)]


def get_gstat():
    print("GSTAT:")
    i = 0
    for reg in read_regs(0x01):
        print("S"+str(i)+": ", end="")
        #print(bin(reg))
        if reg & (1<<0):
            print("reset, ", end="")
        if reg & (1<<1):
            print("drv_err", end="")
        if reg & (1<<2):
            print("uv_cp", end="")
        print("")
        i += 1

# Turn on input
def enable_input():
    # Disable
    with open("/sys/class/gpio/gpio18/value", "w") as f:
        f.write("0\n")
    
    time.sleep(0.01)
    # Enable 
    with open("/sys/class/gpio/gpio18/value", "w") as f:
        f.write("1\n")


def step_xy():
    with open("/sys/class/gpio/gpio110/value", "w") as f:
        f.write("1\n")
    with open("/sys/class/gpio/gpio112/value", "w") as f:
        f.write("1\n")
    with open("/sys/class/gpio/gpio114/value", "w") as f:
        f.write("1\n")
    with open("/sys/class/gpio/gpio110/value", "w") as f:
        f.write("0\n")
    with open("/sys/class/gpio/gpio112/value", "w") as f:
        f.write("0\n")
    with open("/sys/class/gpio/gpio114/value", "w") as f:
        f.write("0\n")
    time.sleep(0.001)
    
def dir(direct):
    with open("/sys/class/gpio/gpio111/value", "w") as f:
        f.write("{}\n".format(direct))
    with open("/sys/class/gpio/gpio113/value", "w") as f:
        f.write("{}\n".format(direct))


def direct_mode():
    A = [-248, 0, 248, 0]
    B = [0, 248, 0, -248]
    for i in range(4):
        write_regs(0x2D, (A[i]<<16)|B[i])
        time.sleep(0.001)

enable_input()
time.sleep(1)

if passing_sanity_test():
    print("Sanity test failed")


#set_chopconf()
#set_pwm_threshold()
#set_hold_current()
#set_gconf()
#set_coolconf()
#get_status(0)


#get_status(0)
#get_drv_status()
#get_status(0)

#print("Chopconf")
#read_chopconf()


i = 0
mres = 0
while 1:
    print("{} {}                                  \r".format(get_tstep(), get_pins()), end="")
    #get_status(0) 
    #direct_mode()
    #reg = read_regs(0x04)[5]
    #print("Pins: "+bin(reg & 0xFF)+"\r", end="")
    #step_xy()
    #if(i%1000 == 0):
    #    set_chopconf((mres % 9))
    #    print("\n{}\n".format((mres % 9)))
    #    dir(mres%2)
    #    mres += 1
    #i +=1

    

