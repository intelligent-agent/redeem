from _PathPlannerNative import PathPlannerNative
from time import sleep
import math

t = PathPlannerNative(1024)

t.initPRU("/root/redeem/firmware/firmware_runtime.bin","/root/redeem/firmware/firmware_endstops.bin")
#t.initPRU("/root/redeem/am335x_pru_package/pru_sw/example_apps/bin/PRU_memAccessPRUDataRam.bin","/root/redeem/firmware/firmware_endstops.bin")
t.setAxisStepsPerMeter(tuple([1000.0]*8))
t.setAcceleration(tuple([0.1]*8))
t.setMaxSpeeds(tuple([1]*8))
t.setMinSpeeds(tuple([0.01]*8))
t.setJerks(tuple([0.01]*8))
t.setPrintMoveBufferWait(250)
t.setMinBufferedMoveTime(100)
t.setMaxBufferedMoveTime(1000)

#t.setAxes(5)
t.runThread()
#t.setBedCompensationMatrix((1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0))
t.setBedCompensationMatrix((1.0, 0.0, 0.01978955219479585, 0.0, 1.0, -0.006212847825189273, -0.019405449540676818, 0.006251693127867221, 1.0))
#t.setBedCompensationMatrix((1.0, 0.0, 0.1, 0.0, 1.0, 0.0, -0.1, 0.0, 1.0))
t.setBedCompensationMatrix((1.0, 0.0, 0.01921552892159129, 0.0, 1.0, -0.008267264546443482, -0.01885318314460967, 0.008336190659107847, 1.0))

#start = (0, 0, 0, 0, 0)
#end = (-1, -1, -1, -1, -1)

#t.queueMove(start, end, 1.0, 1.0, False, False)
#t.waitUntilFinished()
#t.stopThread(True)


# back and forth a few times
speed       = 0.1
accel       = 0.1
cancelable  = False
optimize    = False
enable_soft_endstops = False
use_bed_matrix       = False
use_backlash_compensation = False
tool_axis            = 3
virgin               = True

for i in range(10):
    start = tuple([0.0]*8)
    end = ((i%2)*0.01-0.005, 0, 0, 0, 0, 0, 0, 0)
    t.queueMove(start, end, speed, accel, cancelable,
    optimize, enable_soft_endstops, use_bed_matrix, use_backlash_compensation,
    tool_axis, virgin)

for i in range(45):
    start = (0.1*math.sin(2*math.pi*(i*8)/360), 0.1*math.cos(2*math.pi*(i*8)/360), 0, 0, 0, 0, 0, 0)
    end = (0.1*math.sin(2*math.pi*(i+1*8)/360), 0.1*math.cos(2*math.pi*(i+1*8)/360), 0, 0, 0, 0, 0, 0)
    speed       = 0.00001
    accel       = 0.5
    cancelable  = False
    optimize    = False
    enable_soft_endstops = False
    use_bed_matrix       = True
    use_backlash_compensation = False
    tool_axis            = 3
    virgin               = True
    #t.queueMove(start, end, speed, accel, cancelable,
    #optimize, enable_soft_endstops, use_bed_matrix, use_backlash_compensation,
    #tool_axis, virgin)


# Long Z-move
start       = (0, 0, 0, 0, 0, 0, 0, 0)
end         = (0.1, 0, 0, 0, 0, 0, 0, 0)
speed       = 0.00001
accel       = 0.5
cancelable  = False
optimize    = False
enable_soft_endstops = False
use_bed_matrix       = False
use_backlash_compensation = False
tool_axis            = 3
virgin               = True
#t.queueMove(start, end, speed, accel, cancelable,
#    optimize, enable_soft_endstops, use_bed_matrix, use_backlash_compensation,
#    tool_axis, virgin)

#t.runThread()
t.waitUntilFinished()
t.stopThread(True)

