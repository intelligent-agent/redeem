from PathPlannerNative import PathPlannerNative
from time import sleep

t = PathPlannerNative()

t.initPRU("/root/redeem/firmware/firmware_runtime.bin","/root/redeem/firmware/firmware_endstops.bin")
#t.initPRU("/root/redeem/am335x_pru_package/pru_sw/example_apps/bin/PRU_memAccessPRUDataRam.bin","/root/redeem/firmware/firmware_endstops.bin")


end = (0,0,0,0)

t.runThread()
for i in xrange(1,12):
	start = end
	end2 = (i*10,0,0,0)
	t.queueMove(start,end2,100)
	end = end2

sleep(2) # Time in seconds.

t.stopThread(True)

