from _PathPlannerNative import PathPlannerNative

import time

t = PathPlannerNative(1024)

#t.initPRU("/root/redeem/firmware/firmware_runtime.bin","/root/redeem/firmware/firmware_endstops.bin")
t.initPRU("/root/redeem/am335x_pru_package/pru_sw/example_apps/bin/PRU_memAccessPRUDataRam.bin","/root/redeem/firmware/firmware_endstops.bin")

t.runThread()
time.sleep(1)

start = (0, 0, 0, 0)
end = (1.0, 0, 0, 0)

t.queueMove(start, end, 3000, False, False)
t.waitUntilFinished()

t.stopThread(True)

