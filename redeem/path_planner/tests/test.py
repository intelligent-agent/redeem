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

start = (0, 0, 0, 0, 0)
end = (-1, -1, -1, -1, -1)

t.queueMove(start, end, 1.0, 1.0, False, False)
t.waitUntilFinished()

#start = (0, 0, 0, 0, 0)
#end = (1.0, 1.0, 1.0, 1.0, 1.0)
#t.queueMove(start,end,1,False, False)

t.queueMove(start, end, 3000, False, False)
t.waitUntilFinished()

t.stopThread(True)

