'''
Pru.py file for Replicape. 

Author: Elias Bakken
email: elias.bakken@gmail.com
Website: http://www.hipstercircuits.com
License: BSD

You can use and change this, but keep this heading :)
'''
PRU0_PRU1_INTERRUPT    = 17
PRU1_PRU0_INTERRUPT    = 18
PRU0_ARM_INTERRUPT     = 19
PRU1_ARM_INTERRUPT     = 20
ARM_PRU0_INTERRUPT     = 21
ARM_PRU1_INTERRUPT     = 22

PRUSS0_PRU0_DATARAM    = 0
PRUSS0_PRU1_DATARAM    = 1
PRUSS0_PRU0_IRAM       = 2
PRUSS0_PRU1_IRAM       = 3

PRU0                   = 0
PRU1                   = 1
PRU_EVTOUT0            = 2
PRU_EVTOUT1            = 3
PRU_EVTOUT2            = 4
PRU_EVTOUT3            = 5
PRU_EVTOUT4            = 6
PRU_EVTOUT5            = 7
PRU_EVTOUT6            = 8
PRU_EVTOUT7            = 9

PRU_EVTOUT_0           = 0
PRU_EVTOUT_1           = 1
PRU_EVTOUT_2           = 2
PRU_EVTOUT_3           = 3
PRU_EVTOUT_4           = 4
PRU_EVTOUT_5           = 5
PRU_EVTOUT_6           = 6
PRU_EVTOUT_7           = 7


import os
os.system("export LD_LIBRARY_PATH=/usr/local/lib")
import logging
import pypruss      					                            # The Programmable Realtime Unit Library
import numpy as np						                            # Needed for braiding the pins with the delays
from threading import Thread, Lock
import Queue
import time 
import mmap
import struct 
import select

DDR_MAGIC			= 0xbabe7175

class Pru:
    def __init__(self):
        pru_hz 			    = 200*1000*1000             # The PRU has a speed of 200 MHz
        self.s_pr_inst 		= 1.0/pru_hz                # I take it every instruction is a single cycle instruction
        self.s_pr_inst_2    = 2.0*(1.0/pru_hz)          # I take it every instruction is a single cycle instruction
        self.inst_pr_loop 	= 16                        # This is the minimum number of instructions needed to step. 
        self.inst_pr_delay 	= 2                         # Every loop adds two instructions: i-- and i != 0            
        self.sec_to_inst_dev = (self.s_pr_inst*2)
        self.pru_data       = []      	    	        # This holds all data for one move (x,y,z,e1,e2)
        self.ddr_used       = Queue.Queue(30)           # List of data lengths currently in DDR for execution
        self.ddr_reserved   = 0      
        self.ddr_mem_used   = 0  
        self.clear_events   = []       
        self.ddr_lock       = Lock() 
        self.debug = 0
    
        self.i = 0
        pypruss.modprobe(0x40000)    			        # This only has to be called once pr boot
        self.ddr_addr = pypruss.ddr_addr()
        self.ddr_size = pypruss.ddr_size() 
        print "The DDR memory reserved for the PRU is "+hex(self.ddr_size)+" and has addr "+hex(self.ddr_addr)

        ddr_offset     		= self.ddr_addr-0x10000000  # The Python mmap function cannot accept unsigned longs. 
        ddr_filelen    		= self.ddr_size+0x10000000
        self.DDR_START      = 0x10000000
        self.DDR_END        = 0x10000000+self.ddr_size
        self.ddr_start      = self.DDR_START
        self.ddr_nr_events  = self.ddr_addr+self.ddr_size-4


        with open("/dev/mem", "r+b") as f:	            # Open the memory device
            self.ddr_mem = mmap.mmap(f.fileno(), ddr_filelen, offset=ddr_offset) # mmap the right area            
            self.ddr_mem[self.ddr_start:self.ddr_start+4] = struct.pack('L', 0)  # Add a zero to the first reg to make it wait
       
        pypruss.init()						            # Init the PRU
        pypruss.open(0)						            # Open PRU event 0 which is PRU0_ARM_INTERRUPT
        pypruss.pruintc_init()					        # Init the interrupt controller
        pypruss.pru_write_memory(0, 0, [self.ddr_addr, self.ddr_nr_events])		# Put the ddr address in the first region 
        pypruss.exec_program(0, "../firmware/firmware_pru_0.bin")	# Load firmware "ddr_write.bin" on PRU 0
        self.t = Thread(target=self._wait_for_events)         # Make the thread
        self.running = True
        self.t.start()		                

        logging.debug("PRU initialized")

    ''' Add some data to one of the PRUs '''
    def add_data(self, data):
        (pins, delays) = data                       	    # Get the data
        if len(pins) == 0:
            return 0
        delays = map(self._sec_to_inst, delays)     	    # Convert the delays in secs to delays in instructions
        data = np.array([pins, delays])		        	    # Make a 2D matrix combining the ticks and delays
        data = list(data.transpose().flatten())     	    # Braid the data so every other item is a pin and delay
        if len(self.pru_data) > 0:
            self.pru_data = self._braid_data(data, self.pru_data)
        else:
            self.pru_data = data
        return 1    

    ''' Check if the PRU has capacity for a chunk of data '''
    def has_capacity_for(self, data_len):
        with self.ddr_lock:
            cap = self.ddr_size-self.ddr_mem_used
        return (cap/2.0 > data_len) 

    ''' Check if the PRU has capacity for a chunk of data '''
    def get_capacity(self):
        with self.ddr_lock:
            cap = self.ddr_size-self.ddr_mem_used
        return cap

    def wait_until_done(self):
        ''' Wait until the queue is empty '''
        self.ddr_used.join()        

    ''' Returns True if there are segments on queue '''
    def is_processing(self):
        return (self.ddr_used.qsize() > 0)

    ''' Commit the data to the DDR memory '''
    def commit_data(self, two=False):
        data = struct.pack('L', len(self.pru_data)/2)	    	# Data in string form
        data += ''.join([struct.pack('L', word) for word in self.pru_data])
        data += struct.pack('L', 0)                             # Add a terminating 0, this keeps the fw waiting for a new command.

        self.ddr_end = self.ddr_start+len(data)       
        if self.ddr_end >= self.DDR_END-16:                     # If the data is too long, wrap it around to the start
            multiple = (self.DDR_END-self.ddr_start)%8          # Find a multiple of 8
            cut = self.DDR_END-self.ddr_start-multiple-4-8      # The cut must be done after a delay, so a multiple of 8 bytes +/-4
        
            first = struct.pack('L', len(data[4:cut])/8)+data[4:cut]    # Update the loop count
            first += struct.pack('L', DDR_MAGIC)                        # Add the magic number to force a reset of DDR memory counter
            print "Laying out from "+hex(self.ddr_start)+" to "+hex(self.ddr_start+len(first))
            self.ddr_mem[self.ddr_start:self.ddr_start+len(first)] = first  # Write the first part of the data to the DDR memory.

            with self.ddr_lock:
                self.ddr_mem_used += len(first)
            self.ddr_used.put(len(first))

            if len(data[cut:-4]) > 0:                                 # If len(data) == 4, only the terminating zero is present..
                second = struct.pack('L', (len(data[cut:-4])/8))+data[cut:]     # Add the number of steps in this iteration
                self.ddr_end = self.DDR_START+len(second)           # Update the end counter
                print "Second batch starts from "+hex(self.DDR_START)+" to "+hex(self.ddr_end)
                self.ddr_mem[self.DDR_START:self.ddr_end] = second  # Write the second half of data to the DDR memory.
                with self.ddr_lock:
                    self.ddr_mem_used += len(second)
                self.ddr_used.put(len(second))

            else:
                self.ddr_end = self.DDR_START+4
                self.ddr_mem[self.DDR_START:self.DDR_START+4] = struct.pack('L', 0) # Terminate the first word
                self.debug = 2
                print "\tSecond batch skipped, 0 length"            
        else:
            self.ddr_mem[self.ddr_start:self.ddr_end] = data    # Write the data to the DDR memory. 
            with self.ddr_lock:
                self.ddr_mem_used += len(data)               
            self.ddr_used.put(len(data)) 		            # update the amount of memory used 
            if self.debug > 0:
                 print "Pushed "+str(len(data))+" from "+hex(self.ddr_start)+" to "+hex(self.ddr_end)
            

        self.ddr_start 		= self.ddr_end-4                    # Update the start of ddr for next time 
        self.pru_data 		= []                                # Reset the pru_data list since it has been commited         


    ''' Catch events coming from the PRU '''                
    def _wait_for_events(self):
        events_caught = 0
        self.dev = os.open("/dev/uio0", os.O_RDONLY)
        self.new_events = 0
        self.old_events = 0
        nr_interrupts = 0
        while self.running:
            ret = select.select( [self.dev],[],[], 1.0 )
            if ret[0] == [self.dev]:
                self._wait_for_event()
                pypruss.clear_event(PRU0_ARM_INTERRUPT)			# Clear the event        
                nr_events = struct.unpack("L", self.ddr_mem[self.DDR_END-4:self.DDR_END])[0]            
                while nr_interrupts < nr_events:
                    ddr = self.ddr_used.get()                       # Pop the first ddr memory amount           
                    with self.ddr_lock:
                        self.ddr_mem_used -= ddr                    
                    if self.debug > 0:
                        print "Popped "+str(ddr)+"\tnow "+hex(self.get_capacity())
                    self.ddr_used.task_done()
                    nr_interrupts += 1                         

    ''' Wait for an event. The resturn is the number of events that have occured since last check '''
    def _wait_for_event(self):
        self.new_events =  struct.unpack("L", os.read(self.dev, 4))[0]
        ret = self.new_events-self.old_events
        self.old_events = self.new_events
        return ret

    ''' Close shit up '''
    def join(self):
        logging.debug("joining")
        self.running = False
        self.t.join()        
        self.ddr_mem.close()                                         # Close the memory        
        pypruss.pru_disable(0)                                  # Disable PRU 0, this is already done by the firmware
        pypruss.exit()                                          # Exit, don't know what this does. 
        
    ''' Convert delay in seconds to number of instructions for the PRU '''
    def _sec_to_inst_2(self, s):					    # Shit, I'm missing MGP for this??
        inst_pr_step  = s/self.s_pr_inst  		    # Calculate the number of instructions of delay pr step. 
        inst_pr_step /= 2.0					        # To get a full period, we must divide by two. 
        inst_pr_step -= self.inst_pr_loop		    # Remove the "must include" number of steps
        inst_pr_step /= self.inst_pr_delay		    # Yes, this must be right..
        #inst_pr_step = ((s/self.s_pr_inst)-self.inst_pr_loop)/self.inst_pr_delay
        if inst_pr_step < 1:
            inst_pr_step = 1
        return int(inst_pr_step)			        # Make it an int

    ''' Convert delay in seconds to number of instructions for the PRU '''
    def _sec_to_inst(self, s):					    # Shit, I'm missing MGP for this??
        inst_pr_step = (int(s/self.s_pr_inst_2)-self.inst_pr_loop)/self.inst_pr_delay
        if inst_pr_step < 1:
            inst_pr_step = 1
        if inst_pr_step == 0xbabe7175:
            print "\tInst pr step is BABETITS!!!"
            inst_pr_step = 0xbabe7175-1
        return inst_pr_step

    ''' Braid/merge together the data from the two data sets'''
    def _braid_data(self, data1, data2):
        braids = [data1[0] | data2[0]]
        del data1[0]
        del data2[0]

        while len(data1) > 1 and len(data2) > 1:                        
            if data1[0] > data2[0]:                         # If data 1 is bigger, 
                data1[0]-= data2[0]-self.inst_pr_loop       # remove the delay from data1..
                if data1[0] < 1:
                    data1[0] = 1
                braids += data2[0:2]                        # And insert data2 with 
                del data2[0:2]                              # Delete the pushed data
            elif data1[0] < data2[0]:                       # If data 2 is bigger, 
                data2[0]-= data1[0]-self.inst_pr_loop       # remove the delay from data2..
                if data2[0] < 1:
                    data2[0] = 1
                braids += data1[0:2]                        # And insert data2 with 
                del data1[0:2]
            else:
                braids += [data1[0]]
                braids += [data1[1] | data2[1]]             # Merge the pins
                del data1[0:2]
                del data2[0:2]

        braids += [max(data1[0], data2[0])]
        del data1[0]
        del data2[0]        
        braids += data2
        braids += data1

        return braids



'''
        if two:
            data = struct.pack('L', len(self.pru_data)/2)	    	# Data in string form
            #print list(sum(self.pru_data, ()))
            self.pru_data = [(self._sec_to_inst(x), y) for x, y in self.pru_data]
            data += ''.join([struct.pack('L', word) for word in list(sum(self.pru_data, ()))])
            data += struct.pack('L', 0)                     # Add a terminating 0, this keeps the fw waiting for a new command.

        else:
 '''
