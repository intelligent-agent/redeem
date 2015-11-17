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
#t.setAxes(5)
t.runThread()


#start = (0, 0, 0, 0, 0)
#end = (-1, -1, -1, -1, -1)

#t.queueMove(start, end, 1.0, 1.0, False, False)
#t.waitUntilFinished()
#t.stopThread(True)


for i in range(10):
    start = tuple([0.0]*8)
    end = ((i%2)*0.02-0.01, 0, 0, 0, 0, 0, 0, 0)
    #t.queueMove(start, end, 1.0, 1.0, False, False)
    

for i in range(45):
    start = (0.1*math.sin(2*math.pi*(i*8)/360), 0.1*math.cos(2*math.pi*(i*8)/360), 0, 0, 0, 0, 0, 0)
    end = (0.1*math.sin(2*math.pi*(i+1*8)/360), 0.1*math.cos(2*math.pi*(i+1*8)/360), 0, 0, 0, 0, 0, 0)
    #t.queueMove(start, end, 1.0, 1.0, False, False)


# Long Z-move
start = (0, 0, 0, 0, 0, 0, 0, 0)
end   = (0.01, 0, 0, 0, 0, 0, 0, 0)
t.queueMove(start, end, 0.00001, 0.5, False, False)

#t.runThread()
t.waitUntilFinished()
t.stopThread(True)

