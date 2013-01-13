





#from Gcode import Gcode
from threading import Thread
import select

class USB:
    def __init__(self, queue):
        self.queue = queue
        self.tty = open("/dev/ttyGS0", "r+")
        self.running = True
        self.t = Thread(target=self.get_message)
        self.t.start()		

    # Loop that gets messages and pushes them on the queue
    def get_message(self):
        while self.running:
            ret = select.select( [self.tty],[],[], 1.0 )
    	    if ret[0] == [self.tty]:
                message = self.tty.readline()          
                print "Message: "+message+" ("+message.encode("hex")+")"	
                self.queue.append(message)
            

    # Send a message		
    def send_message(self, message):
        print "USB: writing '"+message+"'"
        if message[-1] != "\n":
            message += "\n"
        self.tty.write(message)

    # Stop receiving mesassages
    def close(self):
        self.running = False
        self.t.join(1.5)

