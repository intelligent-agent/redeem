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

import pypruss      					                            # The Programmable Realtime Unit Library
import numpy as np						                            # Needed for braiding the pins with the delays
from threading import Thread
import time 


DDR_BASEADDR		= 0x70000000					# The actual baseaddr is 0x80000000, but due to a bug(?), 
DDR_HACK			= 0x10001000					# Python accept unsigned int as offset argument.
DDR_FILELEN			= DDR_HACK+0x1000				# The amount of memory to make available
DDR_OFFSET			= DDR_HACK						# Add the hack to the offset as well. 

class Pru:
    def __init__(self):
        pru_hz 			    = 200*1000*1000		                        # The PRU has a speed of 200 MHz
        self.s_pr_inst 		= 1.0/pru_hz		                        # I take it every instruction is a single cycle instruction
        self.inst_pr_loop 	= 16				                        # This is the minimum number of instructions needed to step. 
        self.inst_pr_delay 	= 2					                        # Every loop adds two instructions: i-- and i != 0            
        self.pru_data       = [[], []]
        self.data_set       = [[],[]]                                   # Split the data up into manageble packages 
		with open("/dev/mem", "r+b") as f:					# Open the memory device
			ddr_mem = mmap.mmap(f.fileno(), DDR_FILELEN, offset=DDR_BASEADDR) # 
		
		pypruss.modprobe()							       	# This only has to be called once pr boot
		pypruss.init()										# Init the PRU
		pypruss.open(0)										# Open PRU event 0 which is PRU0_ARM_INTERRUPT
		#pypruss.open(1)										# Open PRU event 0 which is PRU0_ARM_INTERRUPT
		pypruss.pruintc_init()								# Init the interrupt controller
		pypruss.exec_program(0, "./ddr_write.bin")			# Load firmware "ddr_write.bin" on PRU 0
		pypruss.wait_for_event(0)							# Wait for event 0 which is connected to PRU0_ARM_INTERRUPT
		pypruss.clear_event(0)								# Clear the event
        #pypruss.modprobe()							        # Modprobe    
        #pypruss.init_all()								    # Init
        #pypruss.wait_for_both()				            # Wait for the PRUs to finish
        print "PRU initialized"


    ''' Add some data to one of the PRUs '''
    def add_data(self, data, pru_num):
        (pins, delays) = data                       	# Get the data
        if len(pins) == 0:
            return 
        print "Adding data len for "+str(pru_num)+": "+str(len(pins))
        delays = map(self._sec_to_inst, delays)     	# Convert the delays in secs to delays in instructions
        data = np.array([pins, delays])		        	# Make a 2D matrix combining the ticks and delays
        data = list(data.transpose().flatten())     	# Braid the data so every other item is a pin and delay
        
        if len(self.pru_data[pru_num]) > 0:
            self.pru_data[pru_num] = self._braid_data(data, self.pru_data[pru_num])
        else:
            self.pru_data[pru_num] = data
       

	''' Commit the data '''
	def commit_data(self):
		for reg in self.pru_data[0]:
			data += "".join(map(chr, [20, 0, 0, 0]))	# Make the data, it needs to be a string
		ddr_mem[DDR_OFFSET:DDR_OFFSET+4] = data		 	# Write the data to the DDR memory, four bytes should suffice			

	''' Close shit up '''
	def close(self):
		ddr_mem.close()									# Close the memory 
		f.close()										# Close the file
		pypruss.pru_disable(0)								# Disable PRU 0, this is already done by the firmware
		pypruss.pru_disable(1)								# Disable PRU 0, this is already done by the firmware
		pypruss.exit()										# Exit, don't know what this does. 


    ''' slice up the data into nice little packages '''
    def package_data(self):                
        self.data_set = [[], []]                                                        # Reset the data set
        num_packages = max(len(self.pru_data[0])/1024, len(self.pru_data[1])/1024)+1    # Find the length of the biggest data set.
        # TODO: There is a bug here when the package length becomes ~1024. 
        # I think it has to do with the fact that each step takes four * four bytes. 
        # TODO: There is an offset error occuring, don't know why..

        if num_packages > 0:            
            steps_pr_package_0 = ((len(self.pru_data[0])/4)/num_packages)
            steps_pr_package_1 = ((len(self.pru_data[1])/4)/num_packages)
            package_len_0 = steps_pr_package_0*4
            package_len_1 = steps_pr_package_1*4

        for i in range(num_packages):
            self.data_set[0].append([(steps_pr_package_0*2)+1]+self.pru_data[0][0:package_len_0])
            del self.pru_data[0][0:package_len_0]
            self.data_set[1].append([(steps_pr_package_1*2)+1]+self.pru_data[1][0:package_len_1])
            del self.pru_data[1][0:package_len_1]
            print "0: "+str([(steps_pr_package_0*2)+1])+" ... "+ str(len(self.data_set[0][i]))
            print "1: "+str([(steps_pr_package_1*2)+1])+" ... "+ str(len(self.data_set[1][i]))
        
        self.pru_data = [[],[]]                                             # Reset the pru_data list
        
    ''' Enable the pru '''
    def go(self):
        self.t = Thread(target=self._do_work)                   # Make the thread
        self.t.start()		        

    ''' Wait for the PRU to finish '''                
    def wait_for_event(self):
        self.t.join()

    ''' Load the data into the PRUs, wait for them to finish, load some more '''   
    def _do_work(self):
        for i in range(len(self.data_set[0])):
            print "processing package "+str(i)
            pypruss.disable(0)					                # Disable the PRU
            pypruss.disable(1)					                # Disable the PRU
            data = self.data_set[0].pop(0)
            pypruss.write_memory(PRUSS0_PRU0_DATARAM, 0, data)	# Load the data in the PRU ram
            data = self.data_set[1].pop(0)
            pypruss.write_memory(PRUSS0_PRU1_DATARAM, 0, data)	# Load the data in the PRU ram
            pypruss.enable(0)						            # Start the thing
            pypruss.enable(1)						            # Start the thing
            pypruss.wait_for_event(PRU_EVTOUT_0)				    # Wait a while for it to finish.
            pypruss.wait_for_event(PRU_EVTOUT_1)				    # Wait a while for it to finish.    
            pypruss.clear_event(PRU0_ARM_INTERRUPT)				# Clear the event 
            pypruss.clear_event(PRU1_ARM_INTERRUPT)				# Clear the event 
            pypruss.wait_for_event(PRU_EVTOUT_0)				    # Wait a while for it to finish.
            pypruss.wait_for_event(PRU_EVTOUT_1)				    # Wait a while for it to finish.    
            pypruss.clear_event(PRU0_ARM_INTERRUPT)				# Clear the event 
            pypruss.clear_event(PRU1_ARM_INTERRUPT)				# Clear the event 
            
 
    ''' Convert delay in seconds to number of instructions for the PRU '''
    def _sec_to_inst(self, s):					    # Shit, I'm missing MGP for this??
        inst_pr_step  = s/self.s_pr_inst  		    # Calculate the number of instructions of delay pr step. 
        inst_pr_step /= 2.0					        # To get a full period, we must divide by two. 
        inst_pr_step -= self.inst_pr_loop		    # Remove the "must include" number of steps
        inst_pr_step /= self.inst_pr_delay		    # Yes, this must be right..
        if inst_pr_step < 1:
            inst_pr_step = 1
        return int(inst_pr_step)			        # Make it an int


    ''' Braid together the data from the two data sets'''
    def _braid_data(self, data1, data2):
        #print "Braiding "+str(data1)+" and "+str(data2)
        braids = [data1[0] | data2[0]]
        del data1[0]
        del data2[0]
        #print braids

        while len(data1) > 1 and len(data2) > 1:                        
            if data1[0] > data2[0]:                       # If data 1 is bigger, 
                #print "Data 1 is bigger"
                data1[0]-= data2[0]-self.inst_pr_loop        # remove the delay from data1..
                if data1[0] < 1:
                    data1[0] = 1
                                                        #print "adding to braid: "+str([hex(braid) for braid in data2[0:2]])
                braids += data2[0:2]                    # And insert data2 with 
                del data2[0:2]                          # Delete the pushed data
            elif data1[0] < data2[0]:                   # If data 2 is bigger, 
                #print "Data 2 is bigger"
                data2[0]-= data1[0]-self.inst_pr_loop        # remove the delay from data2..
                if data2[0] < 1:
                    data2[0] = 1
                braids += data1[0:2]               # And insert data2 with 
                #print "adding to braid: "+str([hex(braid) for braid in data1[0:2]]) 
                del data1[0:2]
            else:
                #print "Delays are equal"
                braids += [data1[0]]
                braids += [data1[1] | data2[1]]        # Merge the pins
                del data1[0:2]
                del data2[0:2]
            #print braids

        braids += [max(data1[0], data2[0])]
        del data1[0]
        del data2[0]
        
        #print "Finally adding "+str(data1)
        #print "Finally adding "+str(data2)
        braids += data2
        braids += data1
        #print braids
        return braids




        

