'''
Pru.py file for Replicape. 

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''
PRU0_ARM_INTERRUPT     = 19
PRU1_ARM_INTERRUPT     = 20
ARM_PRU0_INTERRUPT     = 21
ARM_PRU1_INTERRUPT     = 22

PRUSS0_PRU0_DATARAM    = 0
PRUSS0_PRU1_DATARAM    = 1
PRUSS0_PRU0_IRAM       = 2
PRUSS0_PRU1_IRAM       = 3
PRUSS0_SHARED_DATARAM  = 4

PRU0                   = 0
PRU1                   = 1

import os
import logging
import pypruss      					                            # The Programmable Realtime Unit Library
import numpy as np						                            # Needed for braiding the pins with the delays
from threading import Thread, Lock
import Queue
import time 
import mmap
import struct 
import select

from collections import deque

DDR_MAGIC			= 0xbabe7175

class Pru:
    ddr_lock = Lock()

    def __init__(self, firmware):
        self.pru_hz		    = 200*1000*1000             # The PRU has a speed of 200 MHz
        self.s_pr_inst      = (1.0/self.pru_hz)          # I take it every instruction is a single cycle instruction
        self.max_delay_cycles = self.pru_hz*4           #Maximum delay to avoid bugs (4 seconds)
        self.pru_data       = []      	    	        # This holds all data for one move (x,y,z,e1,e2)
        self.ddr_used       = Queue.Queue()             # List of data lengths currently in DDR for execution
        self.ddr_reserved   = 0      
        self.ddr_mem_used   = 0  
        self.clear_events   = []       
        self.firmware = firmware

        self.ddr_addr = int(open("/sys/class/uio/uio0/maps/map1/addr","rb").read().rstrip(), 0)
        self.ddr_size = int(open("/sys/class/uio/uio0/maps/map1/size","rb").read().rstrip(), 0)
        logging.info("The DDR memory reserved for the PRU is "+hex(self.ddr_size)+" and has addr "+hex(self.ddr_addr))

        ddr_offset     		= self.ddr_addr-0x20000000  # The Python mmap function cannot accept unsigned longs. 
        ddr_filelen    		= self.ddr_size+0x20000000
        self.DDR_START      = 0x20000000
        self.DDR_END        = 0x20000000+self.ddr_size
        self.ddr_start      = self.DDR_START
        self.ddr_nr_events  = self.ddr_addr+self.ddr_size-4

        with open("/dev/mem", "r+b") as f:	            # Open the memory device
            self.ddr_mem = mmap.mmap(f.fileno(), ddr_filelen, offset=ddr_offset) # mmap the right area            
            self.ddr_mem[self.ddr_start:self.ddr_start+4] = struct.pack('L', 0)  # Add a zero to the first reg to make it wait
       
        self.init_pru();
       
        #Wait until we get the GPIO output in the DDR
        self.dev = os.open("/dev/uio0", os.O_RDONLY)

        ret = select.select( [self.dev],[],[], 1.0 )
        if ret[0] == [self.dev]:
            pypruss.clear_event(PRU0_ARM_INTERRUPT)         # Clear the event        
        
        self.initial_gpio = [struct.unpack("L", self.ddr_mem[self.DDR_START+4:self.DDR_START+8])[0], struct.unpack("L", self.ddr_mem[self.DDR_START+8:self.DDR_START+12])[0], struct.unpack("L", self.ddr_mem[self.DDR_START+12:self.DDR_START+16])[0], struct.unpack("L", self.ddr_mem[self.DDR_START+16:self.DDR_START+20])[0] ]

        os.close(self.dev)

        #Clear DDR
        self.ddr_mem[self.DDR_START+4:self.DDR_START+8] = struct.pack('L', 0)
        self.ddr_mem[self.DDR_START+8:self.DDR_START+12] = struct.pack('L', 0)
        self.ddr_mem[self.DDR_START+12:self.DDR_START+16] = struct.pack('L', 0)
        self.ddr_mem[self.DDR_START+16:self.DDR_START+20] = struct.pack('L', 0)

        self.t = Thread(target=self._wait_for_events)         # Make the thread
        self.t.daemon = True
        self.running = True
        self.t.start()		

    def init_pru(self):
        self.ddr_mem[self.ddr_start:self.ddr_start+4] = struct.pack('L', 0)  # Add a zero to the first reg to make it wait
        pypruss.init()                                  # Init the PRU
        pypruss.open(0)                                 # Open PRU event 0 which is PRU0_ARM_INTERRUPT
        pypruss.open(1)                                 # Open PRU event 1 which is PRU1_ARM_INTERRUPT
        pypruss.pruintc_init()                          # Init the interrupt controller
        pypruss.pru_write_memory(0, 0, [self.ddr_addr, self.ddr_nr_events, 0])      # Put the ddr address in the first region         
        pypruss.exec_program(0, self.firmware.get_firmware(0))                      # Load firmware on PRU 0
        pypruss.exec_program(1, self.firmware.get_firmware(1))                      # Load firmware on PRU 1

    def read_gpio_state(self, gpio_bank):
        """ Return the initial state of a GPIO bank when the PRU was initialized """
        return self.initial_gpio[gpio_bank]
    
    def add_data(self, data):
        """ Add some data to one of the PRUs """
        (pins, dirs, options, delays) = data                       	    # Get the data
        delays = np.clip(np.array(delays)/self.s_pr_inst, 1, self.max_delay_cycles)
        data = np.array([pins,dirs,options, delays.astype(int)])		        	    # Make a 2D matrix combining the ticks and delays
        self.pru_data = data.transpose()   

    def has_capacity_for(self, data_len):
        """ Check if the PRU has capacity for a chunk of data """
        return (self.get_capacity() > data_len)
    
    def get_capacity(self):
        """ Check if the PRU has capacity for a chunk of data """
        return self.ddr_size-self.ddr_mem_used

    def is_empty(self):
        """ If no PRU data is processing, return true """
        self.ddr_used.empty()

    def wait_until_done(self):
        """ Wait until the queue is empty """
        self.ddr_used.join()
    
    def is_processing(self):
        """ Returns True if there are segments on queue """
        return not self.is_empty()

    def pack(self, word):
        return struct.pack('L', word)

    def emergency_interrupt(self):
        pypruss.pru_disable(0)                                  # Disable PRU 0, this is already done by the firmware
        pypruss.exit()                                          # Exit, don't know what this does. 
        logging.debug('Resetting PRU...')
      
        self.pru_data       = []

        while True:
            try:
                b = self.ddr_used.get(block=False)
                if b != None:
                    self.ddr_used.task_done()
            except Queue.Empty:
                break

        self.ddr_reserved   = 0      
        with Pru.ddr_lock: 
            self.ddr_mem_used   = 0  
        self.clear_events   = []       
        self.ddr_start      = self.DDR_START
        self.ddr_nr_events  = self.ddr_addr+self.ddr_size-4

        self.init_pru()

    ''' Commit the data to the DDR memory '''
    def commit_data(self):

        assert len(self.pru_data)/8<self.ddr_size-20

        data = struct.pack('L', len(self.pru_data))	    	# Pack the number of toggles. 
        #Then we have one byte, one byte, one 16 bit (dummy), and one 32 bits
        data += ''.join([struct.pack('BBHL', instr[0],instr[1],instr[2],instr[3]) for instr in self.pru_data])
        data += struct.pack('L', 0)                             # Add a terminating 0, this keeps the fw waiting for a new command.
    
        self.ddr_end = self.ddr_start+len(data)       
        if self.ddr_end >= self.DDR_END-16:                     # If the data is too long, wrap it around to the start
            multiple = (self.DDR_END-16-self.ddr_start)%8       # Find a multiple of 8: 4*(pins, delays)
            cut = self.DDR_END-16-self.ddr_start-multiple-4     # The cut must be done after a delay, so a multiple of 8 bytes +/-4
            
            if cut == 4: 
                logging.error("Cut was 4, setting it to 12")
                cut = 12                
            logging.debug("Data len is "+hex(len(data))+", Cutting the data at "+hex(cut)+" ("+str(cut)+")")

            first = struct.pack('L', len(data[4:cut])/8)+data[4:cut]    # Update the loop count
            first += struct.pack('L', DDR_MAGIC)                        # Add the magic number to force a reset of DDR memory counter
            logging.debug("First batch starts from "+hex(self.ddr_start)+" to "+hex(self.ddr_start+len(first)))
            

            self.ddr_mem[self.ddr_start+4:self.ddr_start+len(first)] = first[4:]  # First write the commands
            self.ddr_mem[self.ddr_start:self.ddr_start+4] = first[0:4]  # Then the commands length (to avoid race condition)

            with Pru.ddr_lock: 
                self.ddr_mem_used += len(first)
            self.ddr_used.put(len(first))

            if len(data[cut:-4]) > 0:                                 # If len(data) == 4, only the terminating zero is present..
                second = struct.pack('L', (len(data[cut:-4])/8))+data[cut:]     # Add the number of steps in this iteration
                self.ddr_end = self.DDR_START+len(second)           # Update the end counter
                logging.debug("Second batch starts from "+hex(self.DDR_START)+" to "+hex(self.ddr_end))
                self.ddr_mem[self.DDR_START+4:self.ddr_end] = second[4:]  # First write the commands
                self.ddr_mem[self.DDR_START:self.DDR_START+4] = second[0:4] # Then the commands length (to avoid race condition)
                


                with Pru.ddr_lock: 
                    self.ddr_mem_used += len(second)
                self.ddr_used.put(len(second))

            else:
                self.ddr_end = self.DDR_START+4
                self.ddr_mem[self.DDR_START:self.ddr_end] = struct.pack('L', 0) # Terminate the first word
                logging.debug("Second batch skipped, 0 length")
            #logging.warning("")
        else:

            self.ddr_mem[self.ddr_start+4:self.ddr_end] = data[4:]    # First write the commands
            self.ddr_mem[self.ddr_start:self.ddr_start+4] = data[0:4]    # Then the commands length (to avoid race condition)
            

            data_len = len(data)
            with Pru.ddr_lock: 
                self.ddr_mem_used += data_len               
            self.ddr_used.put(data_len)                         # update the amount of memory used 
            #logging.debug("Pushed "+str(data_len)+" from "+hex(self.ddr_start)+" to "+hex(self.ddr_end))
            
        self.ddr_start  = self.ddr_end-4    # Update the start of ddr for next time 
        self.pru_data   = []                # Reset the pru_data list since it has been commited         


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
            else:
                nr_events = struct.unpack("L", self.ddr_mem[self.DDR_END-4:self.DDR_END])[0]

            while nr_interrupts < nr_events:
                ddr = self.ddr_used.get()                       # Pop the first ddr memory amount           
                with Pru.ddr_lock: 
                    self.ddr_mem_used -= ddr                    
                #logging.debug("Popped "+str(ddr)+"\tnow "+hex(self.get_capacity()))
                if self.get_capacity() < 0:
                    logging.error("Capacity less than 0!")
                if self.get_capacity() == 0x40000:
                    logging.warning("PRU empty!")                    
                nr_interrupts += 1  
                self.ddr_used.task_done()
                                   

    ''' Wait for an event. The return is the number of events that have occured since last check '''
    def _wait_for_event(self):
        self.new_events =  struct.unpack("L", os.read(self.dev, 4))[0]
        ret = self.new_events-self.old_events
        self.old_events = self.new_events
        return ret

    def force_exit(self):
        self.running = False  
        pypruss.pru_disable(0)                                  # Disable PRU 0, this is already done by the firmware
        pypruss.exit()                                          # Exit, don't know what this does. 

    ''' Close shit up '''
    def join(self):
        logging.debug("joining")
        self.running = False
        self.t.join()        
        self.ddr_mem.close()                                    # Close the memory        
        pypruss.pru_disable(0)                                  # Disable PRU 0, this is already done by the firmware
        pypruss.exit()                                          # Exit, don't know what this does. 
        
