# Measure voltage and current on input

import time
import spidev
spi = spidev.SpiDev()
spi.open(0, 0)


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
    read_regs(0x6C)

def update_status(regs):
    for i in range(6):
        res = get_diag(regs[i*5])
        #if res:
        #    print(res)

def read_regs(reg):
    to_send = [reg, 0x00, 0x00, 0x00, 0x00]*6
    res = spi.xfer(to_send)
    update_status(res)
    to_send = [0x00, 0x00, 0x00, 0x00, 0x00]*6
    regs = spi.xfer(to_send)
    update_status(regs)
    r = [0]*6
    for i in range(6):
        r[i] = regs[i*5+4] | (regs[i*5+3]<<8) | (regs[i*5+2]<<16) | (regs[i*5+1]<<24)
    return r



def write_regs(reg, value):
    to_send = [reg | 0x80, (value & (0xFF<<24))>>24, (value & (0xFF<<16))>>16, (value & (0xFF<<8))>>8, (value & 0xFF)]*6
    print [hex(byte) for byte in to_send]
    res = spi.xfer(to_send)
    update_status(res)

def get_stall_guard_status():
    print("stallguard status: ")
    regs = read_regs(0x6F)
    for r in regs:
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
        if r & (0x1F<<16):
            print("actual motor current: "+str(r & (0x1F<<16)))
        if r & (1<<15):
            print("Full step active")
        if r & (0x1FF):
            print("stallGuard2 result: "+str(r & (0x1FF)))

# Turn on input
def enable_input():
    try:
        with open("/sys/class/gpio/export", "w") as f:
            f.write("18\n")
    except IOError: 
        pass
    with open("/sys/class/gpio/gpio18/direction", "w") as f:
        f.write("out\n")
    with open("/sys/class/gpio/gpio18/value", "w") as f:
        f.write("1\n")

enable_input()
get_status(0)
print "GSTAT:"
i = 0
for reg in read_regs(0x01):
    print "S: "+str(i)
    if reg & 0x01:
        print "reset"
    if reg & 0x02:
        print "drv_err"
    if reg & 0x04:
        print "uv_cp"
    i += 1

write_regs(0x6C, 0x000100C3)
write_regs(0x10, 0x00061F0A)
write_regs(0x11, 0x0000000A)
write_regs(0x00, 0x00000004)
write_regs(0x13, 0x000001F4)
write_regs(0x70, 0x000401C8)

get_status(0)
get_stall_guard_status()
get_status(0)
for reg in read_regs(0x04):
    print("Version: "+hex((reg & 0xff<<24)>>24))
    print("Pins: "+bin(reg & 0xff))

#print "all regs"
#regs = [0x00, 0x01, 0x04, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x2D, 0x33, 0x60, 0x69, 0x6A, 0x6B, 0x6C, 0x6E, 0x6F, 0x70, 0x71, 0x72, 0x73]
#for reg in regs:
#    print read_regs(reg)

