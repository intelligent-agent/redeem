evt_file = open("/dev/input/event0", "rb")
while True:
    evt = evt_file.read(16) # Read the event
    evt_file.read(16)       # Discard the debounce event
    code = ord(evt[10])
    direction  = "down" if ord(evt[12]) else "up"
    print "Switch "+str(code)+" "+direction

