from _PathPlannerMock import PathPlannerMock, PruDump, Delta
from time import sleep
import math

delta = Delta()
delta.setMainDimensions(0.0, 0.304188, 0.146)

t = PathPlannerMock(1024)

t.delta_bot = delta
t.setAxisConfig(3)

t.initPRU("/root/redeem/firmware/firmware_runtime.bin","/root/redeem/firmware/firmware_endstops.bin")
#t.initPRU("/root/redeem/am335x_pru_package/pru_sw/example_apps/bin/PRU_memAccessPRUDataRam.bin","/root/redeem/firmware/firmware_endstops.bin")
t.setAxisStepsPerMeter(tuple([100000.0]*8))
t.setAcceleration(tuple([0.1]*8))
t.setMaxSpeeds(tuple([0.1]*8))
t.setMinSpeeds(tuple([0.0]*8))
t.setJerks(tuple([0.0]*8))
#t.setAxes(5)
t.runThread()
t.setBedCompensationMatrix((1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0))
#t.setBedCompensationMatrix((1.0, 0.0, 0.01978955219479585, 0.0, 1.0, -0.006212847825189273, -0.019405449540676818, 0.006251693127867221, 1.0))
#t.setBedCompensationMatrix((1.0, 0.0, 0.1, 0.0, 1.0, 0.0, -0.1, 0.0, 1.0))
#t.setBedCompensationMatrix((1.0, 0.0, 0.01921552892159129, 0.0, 1.0, -0.008267264546443482, -0.01885318314460967, 0.008336190659107847, 1.0))

#end = (-1, -1, -1, -1, -1)

#t.queueMove(end, 1.0, 1.0, False, False)
#t.waitUntilFinished()
#t.stopThread(True)


#for i in range(10):
#    end = ((i%2)*0.02-0.01, 0, 0, 0, 0, 0, 0, 0)
    #t.queueMove(end, 1.0, 1.0, False, False)
    

#for i in range(45):
    #end = (0.1*math.sin(2*math.pi*(i+1*8)/360), 0.1*math.cos(2*math.pi*(i+1*8)/360), 0, 0, 0, 0, 0, 0)
    #speed       = 0.00001
    #accel       = 0.5
    #cancelable  = False
    #optimize    = False
    #enable_soft_endstops = False
    #use_bed_matrix       = True
    #use_backlash_compensation = False
    #tool_axis            = 3
    #virgin               = True
    #t.queueMove(end, speed, accel, cancelable,
    #optimize, enable_soft_endstops, use_bed_matrix, use_backlash_compensation,
    #tool_axis, virgin)

'''
# Long all-axis move
end         = (0.04, 0.04, 0.04, 0, 0, 0, 0, 0)
speed       = 0.1
accel       = 0.2
cancelable  = False
optimize    = False
enable_soft_endstops = False
use_bed_matrix       = True
use_backlash_compensation = False
tool_axis            = 3
virgin               = True
t.queueMove(end, speed, accel, cancelable,
    optimize, enable_soft_endstops, use_bed_matrix, use_backlash_compensation,
    tool_axis, virgin)

t.waitUntilFinished()
'''

'''
# Shorter move that can't reach full speed
end         = (0.02, 0.02, 0.02, 0, 0, 0, 0, 0)
speed       = 0.1
accel       = 0.2
cancelable  = False
optimize    = False
enable_soft_endstops = False
use_bed_matrix       = True
use_backlash_compensation = False
tool_axis            = 3
virgin               = True
t.queueMove(end, speed, accel, cancelable,
    optimize, enable_soft_endstops, use_bed_matrix, use_backlash_compensation,
    tool_axis, virgin)

t.waitUntilFinished()
'''

t.setState((0, 0, 0, 0, 0, 0, 0, 0))

# Move that's uneven across the axes
end         = (-0.1000, 0.100, 0.100, 0.00, 0, 0, 0, 0)
speed       = 1.0
accel       = 1.0
cancelable  = False
optimize    = False
enable_soft_endstops = False
use_bed_matrix       = True
use_backlash_compensation = False
tool_axis            = 3
virgin               = True
t.queueMove(end, speed, accel, cancelable,
    optimize, enable_soft_endstops, use_bed_matrix, use_backlash_compensation,
    tool_axis)

t.waitUntilFinished()


t.stopThread(True)
pruDump = PruDump.get()
pruDump.test(t)

print(t.getState())

