'''
Path planner for Replicape. Just add paths to 
this and they will be executed as soon as no other 
paths are being executed. 
It's a good idea to stack up maybe five path 
segments, to have a buffer. 

Author: Elias Bakken
email: elias.bakken@gmail.com
Website: http://www.hipstercircuits.com
License: BSD

You can use and change this, but keep this heading :)
'''

import time
import logging
import numpy as np  
from threading import Thread
if __name__ != '__main__':
    from Pru import Pru
import Queue
from collections import defaultdict
#from scipy import weave
#import pyximport; pyximport.install()
import braid

class Path_planner:
    ''' Init the planner '''
    def __init__(self, steppers, current_pos):
        self.steppers    = steppers
        if __name__ != '__main__':
            self.pru         = Pru()                                # Make the PRU
        self.paths       = Queue.Queue(30)                      # Make a queue of paths
        self.current_pos = current_pos                          # Current position in (x, y, z, e)
        self.running     = True                                 # Yes, we are running
        self.pru_data    = []
        self.t           = Thread(target=self._do_work)         # Make the thread
        self.t.start()		                

    ''' Set the acceleration used ''' # Fix me, move this to path
    def set_acceleration(self, acceleration):
        self.acceleration = acceleration

    ''' Add a path segment to the path planner '''        
    def add_path(self, new):        
        if hasattr(self, 'prev'):
            self.prev.set_next(new)
            new.set_prev(self.prev)
        self.prev = new        
        self.paths.put(new)

    ''' Return the number of paths currently on queue '''
    def nr_of_paths(self):
        return self.paths.qsize()

    ''' Set position for an axis '''
    def set_pos(self, axis, val):
        logging.debug("setting %s to %s", axis, str(val))
        self.current_pos[axis] = val
	
    def wait_until_done(self):
        '''Wait until planner is done'''
        self.paths.join()
        logging.debug("paths joined")
        self.pru.wait_until_done()		 
        logging.debug("PRU done")

    ''' This loop pops a path, sends it to the PRU 
    and waits for an event '''
    def _do_work(self):
        while self.running:       
            try: 
                path = self.paths.get(timeout = 1)                            # Get the last path added
                path.set_global_pos(self.current_pos.copy())       # Set the global position of the printer
                all_data = {}
                slowest =  0
                for axis in path.get_axes():                       # Run through all the axes in the path    
                    stepper = self.steppers[axis]                  # Get a handle of  the stepper                    
                    data = self._make_data(path, axis)
                    if len(data[0]) > 0:
                        all_data[axis] = data                      # Generate the timing and pin data                         
                        slowest = max(slowest, sum(data[1]))                                   
                #logging.debug("slowest is "+str(slowest))

                for axis in all_data:                              # Make all axes use the same amount of time
                    packet = all_data[axis]                           
                    delays = np.array(packet[1])
                    diff = (slowest-sum(delays))/len(delays)
                    if diff > 0.00002:
                        for j, delay in enumerate(delays):
                            delays[j] = delay+diff                    
                    data = zip(*(packet[0], delays))
                    #logging.debug(axis+": "+str(data))
                    if len(self.pru_data) == 0:
                        self.pru_data = data
                    else:
                        #self.pru_data += data
                        self.pru_data = self._braid_data(self.pru_data, data)

                #logging.debug("PRU data done")              
                if len(self.pru_data) > 0:                   
                    while not self.pru.has_capacity_for(len(self.pru_data[0])*8):          
                        logging.debug("Pru full")              
                        time.sleep(1)              
         
                    self.pru.add_data(zip(*self.pru_data))
                    self.pru.commit_data()                            # Commit data to ddr

                self.pru_data = []                    
                self.paths.task_done()
            except Queue.Empty:
                #logging.debug("Queue empty")
                pass
    
    
    def _braid_data(self, data1, data2):
        """ Braid/merge together the data from the two data sets"""
        return braid.braid_data_c(data1, data2)
    
    
    '''
    def _braid_data(self, data1, data2):
        """ Braid/merge together the data from the two data sets"""
        return braid._braid_data(data1, data2)


        line = 0
        (pin1, dly1) = data1[line]
        (pin2, dly2) = data2.pop(0)
        while True: 
            dly = min(dly1, dly2)
            dly1 -= dly    
            dly2 -= dly
            try:
                if dly1 == 0 and dly2 == 0:
                    data1[line] = (pin1+pin2, dly)
                    (pin1, dly1) = data1[line+1]
                    (pin2, dly2) = data2.pop(0)
                elif dly1 == 0:
                    data1[line] = (pin1+pin2, dly)
                    (pin1, dly1) = data1[line+1]
                elif dly2 == 0:    
                    data1.insert(line, (pin1+pin2, dly))
                    (pin2, dly2) = data2.pop(0)
                line += 1
            except IndexError, e:
                break

     
            if dly2 > 0:   
                data1[line] =  (data1[line][0], data1[line][1]+dly2)        
            elif dly1 > 0:
                data1[line] = (data1[line][0], data1[line][1]+dly1)  
                data1.pop(line+1)
             
            while len(data2) > 0:
                line += 1
                (pin2, dly2) = data2.pop(0)
                data1.append((pin2+pin1, dly2))
            while len(data1) > line+1:
                line += 1
                (pin1, dly1) = data1[line]
                data1[line] = (pin2+pin1, dly1)

        return data1
    '''   

    '''
    def _braid_data(self, data1, data2):
        """ Braid/merge together the data from the two data sets"""
        
        # do a little type checking in Python
        assert(type(data1) == type([]))
        assert(type(data2) == type([]))
        
        #The c++ code
        code = r"""
        
        int line = 0;           //Current position in the resulting arrays
        int idx1 = 0;           //Current position in data1
        int idx2 = 0;           //Current position in data2
        
        //Variables for extracting tuple-values
        py::tuple tmp_tuple1, tmp_tuple2;
        int pin1, pin2;
        float dly1, dly2;
        
        //Set max size for array. (Is this the correct maximum size?)
        int max_size = data1.size() + data2.size();
        
        // Allocate memory for two arrays of maximum possible size to contain result
        int * pins = (int*) malloc(sizeof(int) * max_size);
        float * delay = (float*) malloc(sizeof(float) * max_size);
            
            
        //Get first tuples from data1 and data2
        tmp_tuple1 = py_to_tuple(PyList_GetItem(data1,idx1), "tmp_tuple1");
        pin1 = tmp_tuple1[0];
        dly1 = tmp_tuple1[1];
        tmp_tuple2 = py_to_tuple(PyList_GetItem(data2,idx2), "tmp_tuple2");
        pin2 = tmp_tuple2[0];
        dly2 = tmp_tuple2[1];
            
            
        while (1) {
            if (dly1 == dly2) {
                //Create resulting pin number
                pins[line] = pin1 + pin2;
                //Create resulting delay
                delay[line] = dly1;
            
                //DEBUG:
                //printf("Added (%d, %.1f) - dly1=dly2\n", pins[line], delay[line]);
                //printf("dly1=%.1f\n",dly1);
                //printf("dly2=%.1f\n",dly2);
                
                //Update line
                line++; 
                
                //Update indexes
                idx1++;
                idx2++;
                
                //Check that there are still items left in both arrays
                if (idx1 >= data1.size() || idx2 >= data2.size())
                    break;
                
                //Get next tuples from data1 and data2
                tmp_tuple1 = py_to_tuple(PyList_GetItem(data1,idx1), "tmp_tuple1");
                pin1 = tmp_tuple1[0];
                dly1 = tmp_tuple1[1];
                tmp_tuple2 = py_to_tuple(PyList_GetItem(data2,idx2), "tmp_tuple2");
                pin2 = tmp_tuple2[0];
                dly2 = tmp_tuple2[1];
        
            }
            
            else if (dly1 > dly2) {
                //Create resulting pin number
                pins[line] = pin1 + pin2;
                //Create resulting delay
                delay[line] = dly2;
                
                //DEBUG:
                //printf("Added (%d, %.1f) - dly1>dly2\n", pins[line], delay[line]);
                //printf("dly1=%.1f\n",dly1);
                //printf("dly2=%.1f\n",dly2);
                //printf("idx1=%d\n",idx1);
                //printf("idx2=%d\n",idx2);
                
                //Update line
                line++; 
                
                //Subtract dly2 from dly1 to get the delay from the last tuple we added
                dly1 -= dly2;
                
                //Increase idx2
                idx2++;
                
                //Check that there are still items left in data2 array
                if (idx2 >= data2.size())
                    break;
                
                //Get next tuple from data2
                tmp_tuple2 = py_to_tuple(PyList_GetItem(data2,idx2), "tmp_tuple2");
                pin2 = tmp_tuple2[0];
                dly2 = tmp_tuple2[1];
            }
            
            else if (dly1 < dly2) {
                //Create resulting pin number
                pins[line] = pin1 + pin2;
                //Create resulting delay
                delay[line] = dly1;
                
                //DEBUG:
                //printf("Added (%d, %.1f) - dly1<dly2\n", pins[line], delay[line]);
                //printf("dly1=%.1f\n",dly1);
                //printf("dly2=%.1f\n",dly2);
                //printf("idx1=%d\n",idx1);
                //printf("idx2=%d\n",idx2);
                
                //Update line
                line++; 
                
                //Subtract dly1 from dly2 to get the delay from the last tuple we added
                dly2 -= dly1;
                
                //Increase idx1
                idx1++;
                
                //Check that there are still items left in data1 array
                if (idx1 >= data1.size())
                    break;
                    
                //Get next tuple from data1
                tmp_tuple1 = py_to_tuple(PyList_GetItem(data1,idx1), "tmp_tuple1");
                pin1 = tmp_tuple1[0];
                dly1 = tmp_tuple1[1];
            }
        }    
        
        //If we are here, then we have gone through at least one of the arrays.
        //Need to check if there are items left in the other array
        
        if (idx1 < data1.size()) 
        {
            pins[line] = pin1;
            delay[line] = dly1;
            line++;
            idx1++;

            //Iterate through any items left in data1
            for (idx1; idx1 < data1.size(); idx1++) 
            {
                //Get tuple from data1
                tmp_tuple1 = py_to_tuple(PyList_GetItem(data1,idx1), "tmp_tuple1");
                pin1 = tmp_tuple1[0];
                dly1 = tmp_tuple1[1]; 
                
                //Add new tuple to result
                pins[line] = pin1;
                delay[line] = dly1;
                
                //Increase indexes
                line++;
            }
        }
        
        if (idx2 < data2.size()) 
        {
            pins[line] = pin2;
            delay[line] = dly2;
            line++;
            idx2++;     
                
                
            //Iterate through any items left in data2
            for (idx2; idx2 < data2.size(); idx2++) 
            {
                //Get tuple from data2
                tmp_tuple2 = py_to_tuple(PyList_GetItem(data2,idx2), "tmp_tuple2");
                pin2 = tmp_tuple2[0];
                dly2 = tmp_tuple2[1]; 
                
                //Add new tuple to result
                pins[line] = pin2;
                delay[line] = dly2;
                
                //Increase indexes
                line++;
            }
        }
        
        
        //Print result for debugging:
        //printf("\nResulting array:\n");
        //for (int i=0; i<line; i++)
        //    printf("(%d, %.1f), ", pins[i], delay[i]);
        
        //printf("\n\n");    
        
        
        //Create a returnable object from the two arrays "pins" and "delay"
        PyObject *pytup;
        PyObject *pylist = PyList_New(line);
        PyObject *item;
        for (int i=0; i<line; i++)
        {
            pytup = PyTuple_New(2);
            item = PyInt_FromLong(pins[i]);
            PyTuple_SetItem(pytup, 0, item);
            item = PyFloat_FromDouble(delay[i]);
            PyTuple_SetItem(pytup, 1, item);
            
            PyList_SetItem(pylist, i, pytup);
        }
        
        //Free allocated memory
        free(pins);
        free(delay);
        
        //Return array
        return_val = pylist;
        """
        
        return weave.inline(code,['data1', 'data2'])
        '''



    
    ''' Join the thread '''
    def exit(self):
        self.running = False
        self.pru.join()
        #logging.debug("pru joined")
        self.t.join()
        #logging.debug("path planner joined")


    ''' Make the data for the PRU or steppers '''
    def _make_data(self, path, axis):  
        #logging.debug("Making data")   
        stepper         = self.steppers[axis]
        steps_pr_meter  = stepper.get_steps_pr_meter()
        vec             = path.get_axis_length(axis)                        # Total travel distance
        num_steps       = int(abs(vec) * steps_pr_meter)                    # Number of steps to tick
        #logging.debug("Numsteps for "+axis+" is "+str(num_steps))
        if num_steps == 0:
            return ([], [])
        step_pin    = stepper.get_step_pin()                            # Get the step pin
        dir_pin     = stepper.get_dir_pin()                             # Get the direction pin
        dir_pin     = 0 if vec < 0 else dir_pin                         # Disable the dir-pin if we are going backwards               
        pins        = [step_pin | dir_pin, dir_pin]*num_steps           # Make the pin states

        s           = abs(path.get_axis_length(axis))                   # Get the length of the vector
        ratio       = path.get_axis_ratio(axis)                         # Ratio is the length of this axis to the total length

        Vm       = path.get_max_speed()*ratio				            # The travelling speed in m/s
        a        = self.acceleration*ratio    		                    # Accelleration in m/s/s
        ds       = 1.0/steps_pr_meter                                   # Delta S, distance in meters travelled pr step.         
        if path.is_type_print_segment():                                # If there is currently a segment being processed, 
            u_start  = ratio*path.get_start_speed()                 	    # The end speed, depends on the angle to the next
        else:
            u_start = 0
        if path.is_type_print_segment():     # If there are paths in queue, we might not have to slow down
            u_end    = ratio*path.get_end_speed()                 	    # The start speed. Depends on the angle to the prev.
        else:
            u_end = 0

        #logging.debug("Max speed for "+axis+" is "+str(Vm))
        #logging.debug("Start speed for "+axis+" is "+str(u_start))
        #logging.debug("End speed for "+axis+" is "+str(u_end))
        tm_start = (Vm-u_start)/a					                    # Calculate the time for when max speed is met. 
        tm_end   = (Vm-u_end)/a					                        # Calculate the time for when max speed is met. 
        sm_start = min(u_start*tm_start + 0.5*a*tm_start**2, s/2.0)     # Calculate the distance traveled when max speed is met
        sm_end   = min(u_end*tm_end + 0.5*a*tm_end**2, s/2.0)           # Calculate the distance traveled when max speed is met

        distances_start  = list(np.arange(0, sm_start, ds))		        # Table of distances                       
        distances_end    = list(np.arange(0, sm_end, ds))		        # Table of distances                       
        timestamps_start = [(-u_start+np.sqrt(2.0*a*ss+u_start**2))/a for ss in distances_start]# When ticks occur
        timestamps_end   = [(-u_end  +np.sqrt(2.0*a*ss+u_end**2))/a for ss in distances_end]# When ticks occur
        delays_start     = np.diff(timestamps_start)/2.0			    # We are more interested in the delays pr second. 
        delays_end       = np.diff(timestamps_end)/2.0			        # We are more interested in the delays pr second.         
        delays_start     = list(np.array([delays_start, delays_start]).transpose().flatten())         
        delays_end       = list(np.array([delays_end, delays_end]).transpose().flatten()) 

        i_steps     = 2*num_steps-len(delays_start)-len(delays_end)     # Find out how many delays are missing
        i_delays    = [(ds/Vm)/2.0]*i_steps  		                    # Make the intermediate steps
        delays      = delays_start+i_delays+delays_end[::-1]            # Add the missing delays. These are max_speed        
        min_delay = 4.0*10**-6		
        for i, d in enumerate(delays): 
            delays[i] = max(min_delay, delays[i])                       # limit delays to 2 ms
        td          = num_steps/steps_pr_meter                          # Calculate the actual travelled distance        
        if vec < 0:                                                     # If the vector is negative, negate it.      
            td     *= -1.0

		# Make sure the dir pin is shifted 650 ns before the step pins
        pins = [dir_pin]+pins
        delays = [650*10**-9]+delays

        # If the axes are X or Y, we need to transform back in case of 
        # H-belt or some other transform. 
        if axis == "X" or axis == "Y":
            (td_x, td_y) = path.stepper_to_axis(td, axis)
            self.current_pos["X"] += td_x 
            self.current_pos["Y"] += td_y 
        else:                        
            self.current_pos[axis] += td                                    # Update the global position vector
        
        #logging.debug("Is at: "+' '.join('%s:%s' % i for i in self.current_pos.iteritems()))
        #logging.debug("pins for "+axis+" is "+str(pins)+" delays: "+str(delays))
        return (pins, delays)                                           # return the pin states and the data


if __name__ == '__main__':
    pp = Path_planner({}, {})
    data1 = [(2, 1), (4, 3), (2, 4), (4, 1)]
    data2 = [(8, 1.5), (16, 4), (8, 4), (16, 1.5)]
    data3 = [(32, 1.5), (64, 4), (32, 4), (64, 1.5)]
    data1 = pp._braid_data(data1, data2)
    print data1
    data1 = pp._braid_data(data1, data3)
    print data1


    import cProfile
    data1 = [(2, 1), (4, 3), (2, 4), (4, 1)]*10000
    data2 = [(8, 1.5), (16, 4), (8, 4), (16, 1.5)]*10000
    data3 = [(32, 1.5), (64, 4), (32, 4), (64, 1.5)]*10000
    
    cProfile.run('pp._braid_data(data1, data2), pp._braid_data(data1, data3)')
    exit(0)
