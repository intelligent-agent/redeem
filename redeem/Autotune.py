"""
Autotune for Redeem

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: GNU GPL v3: http://www.gnu.org/copyleft/gpl.html

 Redeem is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Redeem is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Redeem.  If not, see <http://www.gnu.org/licenses/>.
"""

from threading import Thread
import time
import logging
import numpy

class Autotune:

    def __init__(self, ):        
        self.noise_band = 0.5
        # Steady state starting temperture
        self.steady_temperature = 100.0
        # Degrees to step
        self.output_step = 30.0
        self.peaks_to_discover = 10
        
    def cancel(self):
        self.running = False
        self.t.join()

    def run(self):
        """ Start the PID autotune loop """
        # Reset found peaks
        self.running = True
        self.temps = []
        
        # Start stepping temperatures
        self._tune()

        # Smooth the data
        self.smooth_temps = self.smooth(sel.temps)

        # Discover peaks
        peaks = self._discover_peaks(self.smooth_temps)

        logging.debug(peaks)

    def _tune(self):
        for peak in range(self.peaks_to_discover):
            # Set lower temperature step
            new_temp = self.steady_temperature - self.output_step
            self.heater.set_temperature(new_temp)

            # Wait for target temperature to be reached
            while not self.heater.is_temperature_reached():
                temp = self.heater.get_temperature()
                self.temps.append(temp)
                if not self.running: 
                    return
                time.sleep(1)

            # Set upper temperature step
            new_temp = self.steady_temperature + self.output_step
            self.heater.set_temperature(new_temp)            

            # Wait for target temperature to be reached
            while not self.heater.is_temperature_reached():
                temp = self.heater.get_temperature()
                self.temps.append(temp)
                if not self.running: 
                    return
                time.sleep(1)
            
    def _discover_peaks(self, data):
        c = (diff(sign(diff(data))) < 0).nonzero()[0] + 1 # local max
        return c

    def smooth(x,window_len=11,window='hanning'):
        """smooth the data using a window with requested size.
        
        This method is based on the convolution of a scaled window with the signal.
        The signal is prepared by introducing reflected copies of the signal 
        (with the window size) in both ends so that transient parts are minimized
        in the begining and end part of the output signal.
        
        input:
            x: the input signal 
            window_len: the dimension of the smoothing window; should be an odd integer
            window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
                flat window will produce a moving average smoothing.

        output:
            the smoothed signal
            
        example:

        t=linspace(-2,2,0.1)
        x=sin(t)+randn(len(t))*0.1
        y=smooth(x)
        
        see also: 
        
        numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
        scipy.signal.lfilter
     
        TODO: the window parameter could be the window itself if an array instead of a string
        NOTE: length(output) != length(input), to correct this: return y[(window_len/2-1):-(window_len/2)] instead of just y.
        """

        if x.ndim != 1:
            raise ValueError, "smooth only accepts 1 dimension arrays."

        if x.size < window_len:
            raise ValueError, "Input vector needs to be bigger than window size."


        if window_len<3:
            return x

        if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
            raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"


        s=numpy.r_[x[window_len-1:0:-1],x,x[-1:-window_len:-1]]
        #print(len(s))
        if window == 'flat': #moving average
            w=numpy.ones(window_len,'d')
        else:
            w=eval('numpy.'+window+'(window_len)')

        y=numpy.convolve(w/w.sum(),s,mode='valid')
        return y

    
