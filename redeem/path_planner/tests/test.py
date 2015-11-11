from _PathPlannerNative import PathPlannerNative
from time import sleep

t = PathPlannerNative(1024)

t.initPRU("/root/redeem/firmware/firmware_runtime.bin","/root/redeem/firmware/firmware_endstops.bin")
#t.initPRU("/root/redeem/am335x_pru_package/pru_sw/example_apps/bin/PRU_memAccessPRUDataRam.bin","/root/redeem/firmware/firmware_endstops.bin")
t.setAxisStepsPerMeter((10000.0, 10000.0, 10000.0, 10000.0, 10000.0))
t.setAcceleration((0.1, 1.0, 1.0, 1.0, 1.0))
t.setMaxSpeeds((1.0, 1.0, 1.0, 1.0, 1.0))
t.setMinSpeeds(tuple([0.1]*5))
t.setJerks(tuple([0.1]*5))

t.runThread()

#start = (0, 0, 0, 0, 0)
#end = (-1, -1, -1, -1, -1)

#t.queueMove(start, end, 1.0, 1.0, False, False)
#t.waitUntilFinished()
#t.stopThread(True)


for i in range(10):
    start = (0, 0, 0, 0, 0)
    end = ((i%2)*0.02-0.01, 0, 0, 0, 0)
    #end = (0.1, 0, 0, 0, 0)
    #print start
    #print end
    t.queueMove(start, end, 1.0, 1.0, False, False)
    
#t.runThread()
t.waitUntilFinished()
t.stopThread(True)

