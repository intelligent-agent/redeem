#import sys
#sys.path.append('/home/elias/workspace/redeem/redeem/path_planner')


from _PathPlannerNative import PathPlannerNative
from time import sleep

t = PathPlannerNative(1024)

t.initPRU("/root/redeem/firmware/firmware_runtime.bin","/root/redeem/firmware/firmware_endstops.bin")
#t.initPRU("/root/redeem/am335x_pru_package/pru_sw/example_apps/bin/PRU_memAccessPRUDataRam.bin","/root/redeem/firmware/firmware_endstops.bin")
t.setAxisStepsPerMeter((1000.0, 1000.0, 1000.0, 1000.0, 1000.0))
t.setAcceleration((1.0, 1.0, 1.0, 1.0, 1.0))
t.setMaxFeedrates((1.0, 1.0, 1.0, 1.0, 1.0))	
t.setMaxJerk(1.0)

t.runThread()

start = (0, 0, 0, 0, 0)
end = (1.0, 0, 0, 0, 0)

t.queueMove(start, end, 1.0, False, False)
t.waitUntilFinished()

#start = (0, 0, 0, 0, 0)
#end = (1.0, 1.0, 1.0, 1.0, 1.0)
#t.queueMove(start,end,1,False, False)

#sleep(5) # Time in seconds.
t.waitUntilFinished()

t.stopThread(True)

