from PathPlanner import PathPlannerNative
from time import sleep

t = PathPlannerNative()

start = (0,0,0,0)
end = (100,0,0,0)

t.runThread()

t.queueMove(start,end,100)

sleep(2) # Time in seconds.

t.stopThread(True)

