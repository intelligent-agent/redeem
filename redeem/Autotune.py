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

from __future__ import division, print_function
import time
import logging
import numpy as np
from threading import Thread
try:
    from Gcode import Gcode
except ImportError:
    from redeem.Gcode import Gcode


class Autotune:

    def __init__(self, heater, temp=200.0, cycles=5, g=None, printer=None):        
        self.heater     = heater
        # Steady state starting temperture
        self.steady_temperature = temp
        self.cycles     = cycles
        self.g          = g
        self.printer    = printer
        self.ambient_temp           = 23.2
        self.output_step            = 10.0        # Degrees to step
        self.stable_start_seconds   = 10
        self.sleep                  = 0.1
        self.stable_temp            = 40.0
        self.pre_calibrate_temp     = 200.0
        self.E = 1.0                      # Hysteresis
        
        self.plot_temps = []

    def cancel(self):
        self.running = False

    def send_temperatures(self):
        while self.running:
            m105 = Gcode({"message": "M105", "prot": self.g.prot})
            self.printer.processor.execute(m105)
            answer = m105.get_answer()
            m105.set_answer(answer[2:])  # strip away the "ok"
            self.printer.reply(m105)
            self.plot_temps.append("({}, {:10.4f})".format(time.time(), self.heater.get_temperature_raw() ))
            time.sleep(1)
        logging.debug(self.plot_temps)

    def run(self):
        """ Start the PID autotune loop """
        # Reset found peaks
        self.running = True

        # Start sending thread
        self.t = Thread(target=self.send_temperatures)
        self.t.start()

        # Enable on-off control
        self.has_onoff_control = self.heater.onoff_control
        self.heater.onoff_control = True

        # Set the standard parameters
        self.old_ok_range = self.heater.ok_range
        self.heater.P = 0.5
        self.heater.I = 0.0
        self.heater.D = 0.0
        self.heater.ok_range = 0.5
        self.d = self.bias = 0.5

        if False:
            self.heater.max_power = 0.25
            max_heat_rate = []
            self.heater.set_target_temperature(220)
            while self.heater.get_temperature() < 60:
                time.sleep(0.1)
                max_heat_rate.append("({}, {:10.4f})".format(time.time(), self.heater.get_temperature_raw() ))
            self.heater.set_target_temperature(0)
            logging.debug("Heatup temps: "+str(max_heat_rate))
            self.t.join()
            return 
    
        # Run pre-calibration
        self._pre_calibrate()

        # Start stepping temperatures
        logging.debug("Starting cycles")
        self._tune()
        logging.debug("Tuning data: "+str(self.temps))

        # Smooth the data using hanning window
        self.smooth_temps = self.smooth(np.array(self.temps))

        # Discover peaks
        peaks = self.detect_peaks(self.smooth_temps)
        valleys = self.detect_peaks(self.smooth_temps, valley=True)
        logging.debug("Found peaks: "+str(peaks))
        logging.debug("Found valleys: "+str(valleys))

        # Calculate the new PID values
        self.calculate_PID(self.smooth_temps, peaks, valleys)

        # Set the new PID settings
        self.heater.ok_range = self.old_ok_range
        self.heater.P = self.Kp
        self.heater.I = self.Ki
        self.heater.D = self.Kd
        self.heater.set_target_temperature(0)

        self.heater.onoff_control = self.has_onoff_control

        self.t.join()


    def _pre_calibrate(self):
        logging.debug("Starting pre-calibrate")
        # Wait for temperature to reach < 40 deg.
        self.heater.set_target_temperature(0)
        while self.heater.get_temperature() > self.stable_temp:
            time.sleep(1)

        # Get the noise band from the thermistor
        self.noise_band = self.heater.get_noise_magnitude()
        # Rev B has a very low noise floor, so if 0 is returned, 
        # set it to 0.5 
        self.noise_band = np.maximum(self.noise_band, 0.5)
        logging.debug("Found noise magnitude: "+str(self.noise_band))

        current_temp = self.heater.get_temperature()
        #self.ambient_temp = current_temp
        # Set the heater at 25% max power
        self.heater.max_power = 0.25

        heatup_temps = []

        # Start heating at 25%
        dead_time = 0
        stop_temp = current_temp + self.noise_band
        self.heater.set_target_temperature(self.pre_calibrate_temp)
        while self.heater.get_temperature_raw() < stop_temp:
            time.sleep(0.1)
            dead_time += 0.1
            heatup_temps.append( "({}, {:10.4f})".format(time.time(), self.heater.get_temperature_raw()) )

        logging.debug("Found dead time: "+str(dead_time))


        # Wait for heatup curve to establish
        stop_time = 2*dead_time
        while stop_time > 0:
            time.sleep(1)
            heatup_temps.append("({}, {:10.4f})".format(time.time(), self.heater.get_temperature_raw() ))
            stop_time -= 1

        # (5) Record slope of heat up curve
        delta_temps = []
        delta_times = []
        delta_time = np.minimum(np.maximum(dead_time*4.0, 10.0), 30.0)
        self.delta_time = delta_time
        logging.debug("Starting delta measurements, time: "+str(delta_time))
        while delta_time > 0:
            delta_temps.append(self.heater.get_temperature_raw())
            delta_times.append(time.time())
            time.sleep(0.1)
            delta_time -= 0.1
            heatup_temps.append("({}, {:10.4f})".format(time.time(), self.heater.get_temperature_raw() ))
        
        logging.debug("Stopping delta measurements")

        logging.debug("Heatup temps: "+str(heatup_temps))

        # (6) Calculate heat-up rate        
        heat_rate = (delta_temps[-1]-delta_temps[0])/(delta_times[-1]-delta_times[0])
        logging.debug("heat up rate at 25%: "+str(heat_rate)+" deg/s")

        # (7) Calculate max heat rate
        self.max_heat_rate = heat_rate*4
        #self.max_heat_rate = 3.740
        logging.debug("Max heat rate: "+str(self.max_heat_rate)+" deg/s")

        # (8) Estimate cutoff point
        self.cutoff_band = self.max_heat_rate*dead_time
        logging.debug("Cutoff band: "+str(self.cutoff_band)+" deg")

        # (9) Raise temp until cutoff. 
        cutoff_temp = self.pre_calibrate_temp - self.cutoff_band
        self.heater.max_power = 1.0
        cutoff_temps = []
        cutoff_times = []
        logging.debug("Cutoff temp: "+str(cutoff_temp)+ " deg")
        while self.heater.get_temperature_raw() < cutoff_temp:
            cutoff_temps.append(self.heater.get_temperature_raw())
            cutoff_times.append(time.time())
            time.sleep(0.1)
            
        
        # (10) Calculate slope in degrees/second, store as setpoint_heating_rate
        self.setpoint_heating_rate = (cutoff_temps[-1]-cutoff_temps[-100])/(cutoff_times[-1]-cutoff_times[-100])
        logging.debug("Found setpoint heating rate: "+str(self.setpoint_heating_rate))
        
        if self.setpoint_heating_rate > self.max_heat_rate:
            self.max_heat_rate = self.setpoint_heating_rate
            logging.debug("Updated max heat rate to: "+str(self.setpoint_heating_rate))


        # (11) Set power to zero
        self.heater.set_target_temperature(0)
        logging.debug("Disabling heater and looking for peak")

        # (12) Find temp peak
        highest_temp = self.heater.get_temperature_raw()
        new_temp = highest_temp
        while new_temp >= highest_temp:
            time.sleep(0.1)
            highest_temp = new_temp
            new_temp = self.heater.get_temperature_raw()
        logging.debug("Found max peak: "+str(highest_temp)+" deg")

        # (13) Adding dead time for kicks
        dead_time = highest_temp-20
        while self.heater.get_temperature_raw() > dead_time:
            time.sleep(0.1)

        # (14) Record cooling rates
        logging.debug("Started recording cooling rates")
        cooling_temps = []
        cooling_times = []
        cooldown_temps = []
        # Get 30 seconds of cooling data
        for temp in range(1200):
            cooling_temps.append(self.heater.get_temperature_raw())
            cooling_times.append(time.time())
            time.sleep(0.1)
            cooldown_temps.append("({}, {:10.4f})".format(time.time(), self.heater.get_temperature_raw() ))

        temps = ",".join(cooldown_temps)
        logging.debug("Cooling temps: "+str(temps))

        diffs = np.array([(cooling_temps[200+(i*200)]-cooling_temps[0+(i*200)]) for i in range(5)])
        times = np.array([(cooling_times[200+(i*200)]-cooling_times[0+(i*200)]) for i in range(5)])
        slopes = abs(diffs/times)
        temp_deltas = [cooling_temps[100+(i*200)]-self.ambient_temp for i in range(5)]
        
        # Wait until we are below cutoff-temp, so we can get some traction
        while self.heater.get_temperature_raw() > cutoff_temp - 20.0:
            time.sleep(1)

        # (15) Record setpoint cooling rate
        self.cooling_rate = slopes[0]

        logging.debug("Cooling rate: "+str(self.cooling_rate)+ " deg/s")
        logging.debug("Diffs: "+str(diffs)+ " deg")
        logging.debug("Times: "+str(times)+ " s")
        logging.debug("Cooling rates: "+str(slopes)+ " deg/s")
        logging.debug("Deltas: "+str(temp_deltas)+ " deg")
        
        # (16) Calculate heat_loss_constant
        self.heat_loss_constant = [ slopes[n]/temp_deltas[n] for n in range(len(slopes))]
        logging.debug("Heat loss constant: "+str(self.heat_loss_constant))
        
        # (17) Calculate heat_loss_K
        self.heat_loss_k = np.average(self.heat_loss_constant)
        logging.debug("Heat loss K: "+str(self.heat_loss_k))

        # (18) This is Python, no need to delete squat.

        # (19) Calculate gain skew
        self.gain_skew = np.sqrt(self.setpoint_heating_rate/self.cooling_rate)
        
        logging.debug("Gain skew: "+str(self.gain_skew))

        logging.debug("Pre calibrate done")


    def _tune(self):
        # (1) Calculate rate of heat loss in degrees/second at desired setpoint using heat loss model, 
        setpoint_loss = self.heat_loss_k * (self.steady_temperature - self.ambient_temp)
        logging.debug("Setpoint loss: "+str(setpoint_loss))

        # (2) Calculate setpoint heater power requirement, 
        setpoint_power = setpoint_loss / self.max_heat_rate
        logging.debug("Setpoint_power: "+str(setpoint_power))
        #setpoint_power = 0.5#setpoint_loss / self.max_heat_rate
        #logging.debug("Setpoint_power: "+str(setpoint_power))

        # (3) Calculate high-cycle power 
        high_cycle_power = setpoint_power*(1.0+1.0/(self.gain_skew**2))
        logging.debug("High-cycle_power: "+str(high_cycle_power))
        
        # (4) Check if high-cycle power exceeds max_PWM 
        if high_cycle_power > 1.0: 
            # notify user the heater is too weak to cycle effectively at the chosen setpoint, 
            # and change setpoint_power=max_PWM/2, ignore gain_skew, and use high-cycle power = max_PWM.
            # TODO: fix this
            pass

        # (5) Apply max_PWM heater power until reaching temp=setpoint - cutoff_band 
                
        cutoff_temp = self.steady_temperature - self.cutoff_band
        self.heater.max_power = 1.0
        self.heater.set_target_temperature(self.steady_temperature)
        logging.debug("Cutoff temp: "+str(cutoff_temp)+ " deg")
        while self.heater.get_temperature_raw() < cutoff_temp:
            time.sleep(0.1)
        logging.debug("Cutoff temp reached")

        self.heater.set_target_temperature(0)
        logging.debug("Disabling heater and looking for peak")

        highest_temp = self.heater.get_temperature_raw()
        new_temp = highest_temp
        while new_temp >= highest_temp:
            time.sleep(0.1)
            highest_temp = new_temp
            new_temp = self.heater.get_temperature_raw()
        logging.debug("Found max peak: "+str(highest_temp)+" deg")

        # (6) Apply setpoint_power heater power and hold until stable 
        self.heater.max_power = setpoint_power
        # Set temp to something above the desired. setpoint power should enforce this.
        self.heater.set_target_temperature(230)
        while self.heater.get_noise_magnitude(300) > 1.0:
            time.sleep(1)

        logging.debug("Stable temp reached")

        self.steady_temperature = self.heater.get_temperature()

        # Set the heater power same as fall time
        self.heater.max_power = high_cycle_power

        self.temps = []

        for peak in range(self.cycles):
            logging.debug("Doing cycle: "+str(peak))
            # Set upper temperature step
            new_temp = self.steady_temperature + self.output_step
            self.heater.set_target_temperature(new_temp)
            logging.debug("Setting temp to "+str(new_temp))

            # Wait for target temperature to be reached
            while self.heater.get_temperature() < self.steady_temperature + self.noise_band:
                temp = self.heater.get_temperature()
                self.temps.append(temp)
                if not self.running: 
                    return
                time.sleep(self.sleep)

            # Set lower temperature step
            new_temp = self.steady_temperature - self.output_step
            self.heater.set_target_temperature(new_temp)
            logging.debug("Setting temp to "+str(new_temp))

            # Wait for target temperature to be reached
            while self.heater.get_temperature() > self.steady_temperature - self.noise_band:
                temp = self.heater.get_temperature()
                self.temps.append(temp)
                if not self.running: 
                    return
                time.sleep(self.sleep)

            if peak >= 2:
                smooth = self.smooth(np.array(self.temps))
                peaks = self.detect_peaks(smooth)
                diff = np.diff(smooth[peaks[-2:]])
                logging.debug("Difference between last two peaks: "+str(diff)+" deg. C.")
                print("Difference between last two peaks: "+str(diff)+" deg. C.")
                logging.debug("Setting heater P: "+str(self.heater.P))
        self.heater.max_power = 1.0
                            
    def calculate_PID(self, temps, peaks, valleys):
        abs_max = temps[peaks[-1]]
        abs_min = temps[valleys[-1]]

        logging.debug("Temperature Gain: "+str(abs_max-abs_min)+" deg. C")
        print("Gain: "+str(abs_max-abs_min))


        # Calculate the oscillation period of the peaks
        Pu = (peaks[-1]-peaks[-2])*self.heater.sleep
        # Calculate the ultimate gain 
        Ku = (4.0*self.output_step)/(np.pi*(abs_max-abs_min)/2.0)

        # (12) Calculate amplitude response
        a_single=(abs_max-abs_min)/2
        d_single=(self.output_step)/2 # Is this right?

        #Ku=(4/np.pi) * (d_single / np.sqrt(a_single**2+self.E**2)) 


        logging.debug("Oscillation period: "+str(Pu)+" seconds")
        logging.debug("Ultimate gain: "+str(Ku))
        print("Oscillation period: "+str(Pu))
        print("Ultimate gain: "+str(Ku))

        # Redeem uses 0..1 instead of 0..255
        # TODO: This is probably not right...
        factor = 10.0
        self.Kp = (0.6*Ku)/factor
        self.Ki = (1.2*Ku / Pu)/factor
        self.Kd = (0.075 * Ku * Pu)/factor

        # Tyreus-Luyben: 
        self.Kp=(0.45*Ku)/factor
        self.Ki=(2.2*Ku/Pu)/factor
        self.Kd=(Pu*Ku/6.3)/factor

        self.Ku = Ku
        self.Pu = Pu
        self.max_temp = abs_max
        self.min_temp = abs_min

    def smooth(self, x,window_len=100,window='hanning'):
        """
        smooth the data using a window with requested size.
        
        This method is based on the convolution of a scaled window with the signal.
        The signal is prepared by introducing reflected copies of the signal 
        (with the window size) in both ends so that transient parts are minimized
        in the begining and end part of the output signal.

        Note: this function was taken from the SciPy cookbook: 
        http://wiki.scipy.org/Cookbook/SignalSmooth
               
        """

        if x.size < window_len:
            raise ValueError, "Input vector needs to be bigger than window size."

        if window_len<3:
            return x

        if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
            raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"


        s=np.r_[x[window_len-1:0:-1],x,x[-1:-window_len:-1]]
        #print(len(s))
        if window == 'flat': #moving average
            w=np.ones(window_len,'d')
        else:
            w=eval('np.'+window+'(window_len)')

        y=np.convolve(w/w.sum(),s,mode='valid')
        return y

    


    def detect_peaks(self, x, mph=None, mpd=1, threshold=0, edge='rising',
                     kpsh=False, valley=False, show=False, ax=None):

        __author__ = "Marcos Duarte, https://github.com/demotu/BMC"
        __version__ = "1.0.4"
        __license__ = "MIT"


        """Detect peaks in data based on their amplitude and other features.

        Parameters
        ----------
        x : 1D array_like
            data.
        mph : {None, number}, optional (default = None)
            detect peaks that are greater than minimum peak height.
        mpd : positive integer, optional (default = 1)
            detect peaks that are at least separated by minimum peak distance (in
            number of data).
        threshold : positive number, optional (default = 0)
            detect peaks (valleys) that are greater (smaller) than `threshold`
            in relation to their immediate neighbors.
        edge : {None, 'rising', 'falling', 'both'}, optional (default = 'rising')
            for a flat peak, keep only the rising edge ('rising'), only the
            falling edge ('falling'), both edges ('both'), or don't detect a
            flat peak (None).
        kpsh : bool, optional (default = False)
            keep peaks with same height even if they are closer than `mpd`.
        valley : bool, optional (default = False)
            if True (1), detect valleys (local minima) instead of peaks.
        show : bool, optional (default = False)
            if True (1), plot data in matplotlib figure.
        ax : a matplotlib.axes.Axes instance, optional (default = None).

        Returns
        -------
        ind : 1D array_like
            indeces of the peaks in `x`.

        Notes
        -----
        The detection of valleys instead of peaks is performed internally by simply
        negating the data: `ind_valleys = detect_peaks(-x)`
        
        The function can handle NaN's 

        See this IPython Notebook [1]_.

        References
        ----------
        .. [1] http://nbviewer.ipython.org/github/demotu/BMC/blob/master/notebooks/DetectPeaks.ipynb       
        """

        x = np.atleast_1d(x).astype('float64')
        if x.size < 3:
            return np.array([], dtype=int)
        if valley:
            x = -x
        # find indices of all peaks
        dx = x[1:] - x[:-1]
        # handle NaN's
        indnan = np.where(np.isnan(x))[0]
        if indnan.size:
            x[indnan] = np.inf
            dx[np.where(np.isnan(dx))[0]] = np.inf
        ine, ire, ife = np.array([[], [], []], dtype=int)
        if not edge:
            ine = np.where((np.hstack((dx, 0)) < 0) & (np.hstack((0, dx)) > 0))[0]
        else:
            if edge.lower() in ['rising', 'both']:
                ire = np.where((np.hstack((dx, 0)) <= 0) & (np.hstack((0, dx)) > 0))[0]
            if edge.lower() in ['falling', 'both']:
                ife = np.where((np.hstack((dx, 0)) < 0) & (np.hstack((0, dx)) >= 0))[0]
        ind = np.unique(np.hstack((ine, ire, ife)))
        # handle NaN's
        if ind.size and indnan.size:
            # NaN's and values close to NaN's cannot be peaks
            ind = ind[np.in1d(ind, np.unique(np.hstack((indnan, indnan-1, indnan+1))), invert=True)]
        # first and last values of x cannot be peaks
        if ind.size and ind[0] == 0:
            ind = ind[1:]
        if ind.size and ind[-1] == x.size-1:
            ind = ind[:-1]
        # remove peaks < minimum peak height
        if ind.size and mph is not None:
            ind = ind[x[ind] >= mph]
        # remove peaks - neighbors < threshold
        if ind.size and threshold > 0:
            dx = np.min(np.vstack([x[ind]-x[ind-1], x[ind]-x[ind+1]]), axis=0)
            ind = np.delete(ind, np.where(dx < threshold)[0])
        # detect small peaks closer than minimum peak distance
        if ind.size and mpd > 1:
            ind = ind[np.argsort(x[ind])][::-1]  # sort ind by peak height
            idel = np.zeros(ind.size, dtype=bool)
            for i in range(ind.size):
                if not idel[i]:
                    # keep peaks with the same height if kpsh is True
                    idel = idel | (ind >= ind[i] - mpd) & (ind <= ind[i] + mpd) \
                        & (x[ind[i]] > x[ind] if kpsh else True)
                    idel[i] = 0  # Keep current peak
            # remove the small peaks and sort back the indices by their occurrence
            ind = np.sort(ind[~idel])

        if show:
            if indnan.size:
                x[indnan] = np.nan
            if valley:
                x = -x
            self._plot(x, mph, mpd, threshold, edge, valley, ax, ind)

        return ind

    def _plot(self, x, mph, mpd, threshold, edge, valley, ax, ind):
        """Plot results of the detect_peaks function, see its help."""
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print('matplotlib is not available.')
        else:
            if ax is None:
                _, ax = plt.subplots(1, 1, figsize=(8, 4))

            ax.plot(x, 'b', lw=1)
            if ind.size:
                label = 'valley' if valley else 'peak'
                label = label + 's' if ind.size > 1 else label
                ax.plot(ind, x[ind], '+', mfc=None, mec='r', mew=2, ms=8,
                        label='%d %s' % (ind.size, label))
                ax.legend(loc='best', framealpha=.5, numpoints=1)
            ax.set_xlim(-.02*x.size, x.size*1.02-1)
            ymin, ymax = x[np.isfinite(x)].min(), x[np.isfinite(x)].max()
            yrange = ymax - ymin if ymax > ymin else 1
            ax.set_ylim(ymin - 0.1*yrange, ymax + 0.1*yrange)
            ax.set_xlabel('Data #', fontsize=14)
            ax.set_ylabel('Amplitude', fontsize=14)
            mode = 'Valley detection' if valley else 'Peak detection'
            ax.set_title("%s (mph=%s, mpd=%d, threshold=%s, edge='%s')"
                         % (mode, str(mph), mpd, str(threshold), edge))
            # plt.grid()
            plt.show()


    def plot2(self, x):
        """Plot results of the detect_peaks function, see its help."""
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print('matplotlib is not available.')
        else:
            _, ax = plt.subplots(1, 1, figsize=(8, 4))

            ax.plot(x, 'b', lw=1)
            ax.set_xlim(-.02*x.size, x.size*1.02-1)
            ymin, ymax = x[np.isfinite(x)].min(), x[np.isfinite(x)].max()
            yrange = ymax - ymin if ymax > ymin else 1
            ax.set_ylim(ymin - 0.1*yrange, ymax + 0.1*yrange)
            ax.set_xlabel('Data #', fontsize=14)
            ax.set_ylabel('Amplitude', fontsize=14)
            # plt.grid()
            plt.show()

if __name__ == '__main__':
    import matplotlib.pyplot as plt

    data = np.array( [99.491650000000007, 99.491650000000007, 99.25, 99.25, 99.25, 99.008350000000007, 99.008350000000007, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 99.008349999999993, 99.008349999999993, 99.25, 99.25, 99.25, 99.491649999999993, 99.491649999999993, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.974975000000001, 99.974975000000001, 99.974975000000001, 100.21665, 100.21665, 100.458325, 100.458325, 100.458325, 100.94175000000001, 100.94175000000001, 101.18350000000001, 101.18350000000001, 101.66674999999999, 101.66674999999999, 101.66674999999999, 102.14999999999999, 102.14999999999999, 102.39149999999999, 102.39149999999999, 102.87475000000001, 102.87475000000001, 102.87475000000001, 103.1165, 103.1165, 103.59999999999999, 103.59999999999999, 104.0835, 104.0835, 104.0835, 104.56675, 104.56675, 105.05, 105.05, 105.53325, 105.53325, 105.53325, 106.01650000000001, 106.01650000000001, 106.5, 106.5, 106.98349999999999, 106.98349999999999, 106.98349999999999, 107.46674999999999, 107.46674999999999, 107.95, 107.95, 108.43325000000002, 108.43325000000002, 108.91650000000001, 108.91650000000001, 108.91650000000001, 109.15825000000001, 109.15825000000001, 109.64175000000002, 109.64175000000002, 109.88350000000001, 109.88350000000001, 109.88350000000001, 110.36675, 110.36675, 110.84999999999999, 110.84999999999999, 111.0915, 111.0915, 111.57475000000001, 111.57475000000001, 111.57475000000001, 111.8165, 111.8165, 112.05825, 112.05825, 112.54174999999999, 112.54174999999999, 112.54174999999999, 112.78349999999999, 112.78349999999999, 113.02525, 113.02525, 113.267, 113.267, 113.267, 113.5085, 113.5085, 113.75, 113.75, 113.9915, 113.9915, 114.233, 114.233, 114.233, 114.233, 114.233, 114.47475, 114.47475, 114.7165, 114.7165, 114.7165, 114.95824999999999, 114.95824999999999, 115.2, 115.2, 115.44175000000001, 115.44175000000001, 115.44175000000001, 115.68350000000001, 115.68350000000001, 115.92525000000001, 115.92525000000001, 116.167, 116.167, 116.167, 116.167, 116.167, 116.40849999999999, 116.40849999999999, 116.64999999999999, 116.64999999999999, 116.89149999999999, 116.89149999999999, 116.89149999999999, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.37475000000001, 117.37475000000001, 117.6165, 117.6165, 117.85825, 117.85825, 117.85825, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.34174999999999, 118.34174999999999, 118.5835, 118.5835, 118.82525, 118.82525, 118.82525, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.3085, 119.3085, 119.3085, 119.55, 119.55, 119.7915, 119.7915, 119.7915, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 120.033, 119.7915, 119.7915, 119.7915, 119.7915, 119.7915, 119.55, 119.55, 119.3085, 119.3085, 119.3085, 119.3085, 119.3085, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 118.82524999999998, 118.82524999999998, 118.58349999999999, 118.58349999999999, 118.34174999999999, 118.34174999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 117.85824999999998, 117.85824999999998, 117.85824999999998, 117.61649999999999, 117.61649999999999, 117.37474999999999, 117.37474999999999, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 116.89150000000001, 116.89150000000001, 116.65000000000001, 116.65000000000001, 116.4085, 116.4085, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 115.92524999999999, 115.92524999999999, 115.92524999999999, 115.6835, 115.6835, 115.44175, 115.44175, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 114.95825000000001, 114.95825000000001, 114.95825000000001, 114.71650000000001, 114.71650000000001, 114.47475, 114.47475, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 113.9915, 113.9915, 113.75, 113.75, 113.75, 113.5085, 113.5085, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.02525, 113.02525, 113.02525, 112.7835, 112.7835, 112.54175000000001, 112.54175000000001, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.05824999999999, 112.05824999999999, 111.81649999999999, 111.81649999999999, 111.57474999999999, 111.57474999999999, 111.57474999999999, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.09150000000001, 111.09150000000001, 111.09150000000001, 110.85000000000001, 110.85000000000001, 110.60850000000001, 110.60850000000001, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.12524999999999, 110.12524999999999, 110.12524999999999, 109.8835, 109.8835, 109.64175, 109.64175, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.15825000000001, 109.15825000000001, 109.15825000000001, 109.15825000000001, 109.15825000000001, 108.91650000000001, 108.91650000000001, 108.67475, 108.67475, 108.67475, 108.67475, 108.67475, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.1915, 108.1915, 108.1915, 107.95, 107.95, 107.7085, 107.7085, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.22525, 107.22525, 106.98349999999999, 106.98349999999999, 106.74175, 106.74175, 106.74175, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.25825, 106.25825, 106.01650000000001, 106.01650000000001, 105.77475000000001, 105.77475000000001, 105.77475000000001, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.2915, 105.2915, 105.2915, 105.05, 105.05, 104.8085, 104.8085, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.32524999999998, 104.32524999999998, 104.08349999999999, 104.08349999999999, 103.84174999999999, 103.84174999999999, 103.84174999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.35824999999998, 103.35824999999998, 103.11649999999999, 103.11649999999999, 102.87474999999999, 102.87474999999999, 102.87474999999999, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.39150000000001, 102.39150000000001, 102.39150000000001, 102.15000000000001, 102.15000000000001, 101.9085, 101.9085, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.42524999999999, 101.42524999999999, 101.1835, 101.1835, 100.94175, 100.94175, 100.94175, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.458325, 100.458325, 100.21665, 100.21665, 100.21665, 99.974975000000001, 99.974975000000001, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.491650000000007, 99.491650000000007, 99.491650000000007, 99.25, 99.25, 99.008350000000007, 99.008350000000007, 99.008350000000007, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 98.7667, 99.008349999999993, 99.008349999999993, 99.25, 99.25, 99.25, 99.491649999999993, 99.491649999999993, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.974975000000001, 99.974975000000001, 99.974975000000001, 100.21665, 100.21665, 100.458325, 100.458325, 100.458325, 100.94175000000001, 100.94175000000001, 101.18350000000001, 101.18350000000001, 101.42525000000001, 101.42525000000001, 101.42525000000001, 101.90849999999999, 101.90849999999999, 102.14999999999999, 102.14999999999999, 102.63325, 102.63325, 102.63325, 103.1165, 103.1165, 103.59999999999999, 103.59999999999999, 104.0835, 104.0835, 104.0835, 104.56675, 104.56675, 105.05, 105.05, 105.2915, 105.2915, 105.2915, 105.77475, 105.77475, 106.01650000000001, 106.01650000000001, 106.5, 106.5, 106.5, 106.98349999999999, 106.98349999999999, 107.46674999999999, 107.46674999999999, 107.95, 107.95, 108.1915, 108.1915, 108.1915, 108.67475000000002, 108.67475000000002, 108.91650000000001, 108.91650000000001, 109.15825000000001, 109.15825000000001, 109.15825000000001, 109.64175000000002, 109.64175000000002, 109.88350000000001, 109.88350000000001, 110.36675, 110.36675, 110.36675, 110.84999999999999, 110.84999999999999, 111.0915, 111.0915, 111.333, 111.333, 111.333, 111.57475000000001, 111.57475000000001, 111.8165, 111.8165, 112.05825, 112.05825, 112.05825, 112.54174999999999, 112.54174999999999, 112.78349999999999, 112.78349999999999, 113.02525, 113.02525, 113.267, 113.267, 113.267, 113.5085, 113.5085, 113.75, 113.75, 113.75, 113.9915, 113.9915, 114.233, 114.233, 114.233, 114.233, 114.233, 114.47475, 114.47475, 114.7165, 114.7165, 114.95824999999999, 114.95824999999999, 114.95824999999999, 115.2, 115.2, 115.2, 115.2, 115.44175000000001, 115.44175000000001, 115.68350000000001, 115.68350000000001, 115.68350000000001, 115.92525000000001, 115.92525000000001, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.40849999999999, 116.40849999999999, 116.64999999999999, 116.64999999999999, 116.64999999999999, 116.89149999999999, 116.89149999999999, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.37475000000001, 117.37475000000001, 117.6165, 117.6165, 117.6165, 117.85825, 117.85825, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.34174999999999, 118.34174999999999, 118.5835, 118.5835, 118.82525, 118.82525, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 119.06699999999999, 118.82524999999998, 118.82524999999998, 118.82524999999998, 118.58349999999999, 118.58349999999999, 118.34174999999999, 118.34174999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 118.09999999999999, 117.85824999999998, 117.85824999999998, 117.61649999999999, 117.61649999999999, 117.37474999999999, 117.37474999999999, 117.37474999999999, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 117.133, 116.89150000000001, 116.89150000000001, 116.65000000000001, 116.65000000000001, 116.4085, 116.4085, 116.4085, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 116.167, 115.92524999999999, 115.92524999999999, 115.92524999999999, 115.6835, 115.6835, 115.44175, 115.44175, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 115.2, 114.95825000000001, 114.95825000000001, 114.71650000000001, 114.71650000000001, 114.47475, 114.47475, 114.47475, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 114.233, 113.9915, 113.9915, 113.75, 113.75, 113.75, 113.5085, 113.5085, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.267, 113.02525, 113.02525, 113.02525, 112.7835, 112.7835, 112.54175000000001, 112.54175000000001, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.3, 112.05824999999999, 112.05824999999999, 111.81649999999999, 111.81649999999999, 111.81649999999999, 111.57474999999999, 111.57474999999999, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.333, 111.09150000000001, 111.09150000000001, 110.85000000000001, 110.85000000000001, 110.60850000000001, 110.60850000000001, 110.60850000000001, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.367, 110.12524999999999, 110.12524999999999, 110.12524999999999, 109.8835, 109.8835, 109.64175, 109.64175, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.40000000000001, 109.15825000000001, 109.15825000000001, 109.15825000000001, 108.9165, 108.9165, 108.67475, 108.67475, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.43300000000001, 108.1915, 108.1915, 108.1915, 107.95, 107.95, 107.7085, 107.7085, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.467, 107.22525, 107.22525, 106.98349999999999, 106.98349999999999, 106.74175, 106.74175, 106.74175, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.5, 106.25825, 106.25825, 106.01650000000001, 106.01650000000001, 105.77475000000001, 105.77475000000001, 105.77475000000001, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.533, 105.2915, 105.2915, 105.05, 105.05, 105.05, 104.8085, 104.8085, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.56699999999999, 104.32524999999998, 104.32524999999998, 104.32524999999998, 104.08349999999999, 104.08349999999999, 103.84174999999999, 103.84174999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.35824999999998, 103.35824999999998, 103.11649999999999, 103.11649999999999, 103.11649999999999, 102.87474999999999, 102.87474999999999, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.633, 102.39150000000001, 102.39150000000001, 102.39150000000001, 102.15000000000001, 102.15000000000001, 101.9085, 101.9085, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.667, 101.42524999999999, 101.42524999999999, 101.42525000000001, 101.42525000000001, 101.42525000000001, 101.1835, 101.1835, 100.94175, 100.94175, 100.94175, 100.94175, 100.94175, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.458325, 100.458325, 100.21665, 100.21665, 100.21665, 99.974975000000001, 99.974975000000001, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333, 99.7333])
    data = np.array( [193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 
193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 
193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 
193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.74175, 193.74175, 193.98349999999999, 193.98349999999999, 
193.98349999999999, 194.22524999999999, 194.22524999999999, 194.46700000000001, 194.46700000000001, 194.46700000000001, 
194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 
194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 
194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 
194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 
194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 
194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 
194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 
194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.70850000000002, 194.70850000000002, 
194.70850000000002, 194.70849999999999, 194.70849999999999, 194.70849999999999, 194.70849999999999, 194.94999999999999, 
194.94999999999999, 194.94999999999999, 194.94999999999999, 194.94999999999999, 195.19149999999999, 195.19149999999999, 
195.43299999999999, 195.43299999999999, 195.19149999999999, 195.19149999999999, 195.19149999999999, 195.19149999999999, 
195.19149999999999, 195.19149999999999, 195.19149999999999, 195.19149999999999, 195.19149999999999, 195.19149999999999, 
195.19149999999999, 195.19149999999999, 194.94999999999999, 194.94999999999999, 194.70849999999999, 194.70849999999999, 
194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 
194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 
194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 
194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 
194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 
194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 
194.46700000000001, 194.22525000000002, 194.22525000000002, 194.22525000000002, 193.98349999999999, 193.98349999999999, 
193.74175, 193.74175, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 
193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.25825, 193.25825, 193.25825, 193.01650000000001, 193.01650000000001,
 192.77475000000001, 192.77475000000001, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 
192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 
192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.29149999999998, 192.29149999999998, 
192.29149999999998, 192.05000000000001, 192.05000000000001, 191.80850000000001, 191.80850000000001, 191.56700000000001, 
191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 
191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 
191.56700000000001, 191.32525000000001, 191.32525000000001, 191.08350000000002, 191.08350000000002, 190.84175000000002, 
190.84175000000002,190.84175000000002, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 
190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 
190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 
190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 
190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 
190.35825, 190.35825, 190.35825, 190.35825, 190.35825, 190.35825, 190.35825, 190.35825, 190.35825, 190.59999999999999, 
190.59999999999999, 190.35825, 190.35825, 190.35825, 190.1165, 190.1165, 189.87475000000001, 189.87475000000001, 
189.87475000000001, 189.87475000000001, 189.87475000000001, 190.1165, 190.1165, 190.1165, 190.1165, 190.1165, 190.1165, 
190.1165, 190.1165, 190.1165, 190.1165, 190.1165, 190.35825, 190.35825, 190.35825, 190.59999999999999, 190.59999999999999, 
190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 
190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 
190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 
190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 
190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 
190.84174999999999, 190.84174999999999, 191.08350000000002, 191.08350000000002, 191.32525000000001, 191.32525000000001, 
191.32525000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 
191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 
191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 
191.56700000000001, 191.80850000000001, 191.80850000000001, 191.80850000000001, 191.80850000000001, 191.80850000000001, 
192.05000000000001, 192.05000000000001, 192.05000000000001, 192.05000000000001, 192.05000000000001, 192.05000000000001, 
192.05000000000001, 192.29150000000001, 192.29150000000001, 192.29150000000001, 192.29150000000001, 192.29150000000001, 
192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.77474999999998, 192.77474999999998, 
192.77474999999998, 192.77475000000001, 192.77475000000001, 193.01650000000001, 193.01650000000001, 193.01650000000001, 
193.25825, 193.25825, 193.25825, 193.25825, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 
193.5, 193.74175, 193.74175, 193.98349999999999, 193.98349999999999, 193.98349999999999, 194.22524999999999, 
194.22524999999999, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 
194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.70850000000002, 194.70850000000002, 
194.70850000000002, 194.94999999999999, 194.94999999999999, 195.19149999999999, 195.19149999999999, 195.43299999999999, 
195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 
195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.67474999999999, 
195.67474999999999, 195.91649999999998, 195.91649999999998, 195.91649999999998, 196.15824999999998, 196.15824999999998, 
196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 
196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 
196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 
196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 
196.40000000000001, 196.40000000000001, 196.64175, 196.64175, 196.8835, 196.8835, 196.8835, 196.8835, 196.8835, 
197.12524999999999, 197.12524999999999, 196.8835, 196.8835, 196.8835, 196.8835, 196.8835, 197.12524999999999, 
197.12524999999999, 197.12524999999999, 197.12524999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 
197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 
197.36699999999999, 197.36699999999999, 197.36699999999999, 197.12524999999999, 197.12524999999999, 197.12524999999999, 
197.12524999999999, 197.12524999999999, 196.8835, 196.8835, 196.8835, 196.8835, 196.8835, 196.8835, 196.8835, 196.64175, 
196.64175, 196.64175, 196.64175, 196.64175, 196.64175, 196.64175, 196.64175, 196.64175, 196.64175, 196.64175, 196.64175, 
196.64175, 196.64175, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 
196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 
196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 
196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.15825000000001, 196.15825000000001, 
195.91649999999998, 195.91649999999998, 
195.67474999999999, 195.67474999999999, 195.67474999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 
195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 
195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 
195.43299999999999, 195.43299999999999, 195.43299999999999, 195.19149999999999, 195.19149999999999, 194.94999999999999, 
194.94999999999999, 194.94999999999999, 194.70849999999999, 194.70849999999999, 194.46700000000001, 194.46700000000001, 
194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 
194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.22525000000002, 194.22525000000002, 
193.98349999999999, 193.98349999999999, 193.74175, 193.74175, 193.74175, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 
193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.25825, 193.25825, 193.01650000000001, 193.01650000000001, 
192.77475000000001, 192.77475000000001, 192.77475000000001, 192.53299999999999, 192.53299999999999, 192.53299999999999, 
192.53299999999999, 192.53299999999999, 192.53299999999999, 192.29149999999998, 192.29149999999998, 192.29149999999998, 
192.05000000000001, 192.05000000000001, 191.80850000000001, 191.80850000000001, 191.56700000000001, 191.56700000000001, 
191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 
191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.32525000000001, 191.32525000000001, 
191.08350000000002, 191.08350000000002, 191.08350000000002, 190.84175000000002, 190.84175000000002, 190.59999999999999, 
190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 
190.59999999999999, 190.59999999999999, 190.35825, 190.35825, 190.1165, 190.1165, 190.1165, 189.87475000000001, 
189.87475000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 
189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 
189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 
189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 
189.63300000000001, 189.63300000000001, 189.39150000000001, 189.39150000000001, 189.39150000000001, 189.39150000000001, 
189.39150000000001, 189.15000000000001, 189.15000000000001, 188.9085, 188.9085, 188.9085, 188.9085, 188.9085, 188.667, 
188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 
188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 
188.667, 188.667, 188.667, 188.9085, 188.9085, 189.15000000000001, 189.15000000000001, 189.15000000000001, 
189.15000000000001, 189.15000000000001, 189.39150000000001, 189.39150000000001, 189.39150000000001, 189.39150000000001, 
189.39150000000001, 189.39150000000001, 189.39150000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 
189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 
189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 
189.63300000000001, 189.63300000000001, 189.87475000000001, 189.87475000000001, 189.87475000000001, 189.87475000000001, 
190.1165, 190.1165, 190.1165, 190.35825, 190.35825, 190.35825, 190.35825, 190.59999999999999, 190.59999999999999, 
190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 
190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 
190.59999999999999, 190.59999999999999, 190.84174999999999, 190.84174999999999, 190.84174999999999, 191.08350000000002, 
191.08350000000002, 191.32525000000001, 191.32525000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 
191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 
191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 
191.56700000000001, 191.80850000000001, 191.80850000000001, 191.80850000000001, 192.05000000000001, 192.05000000000001, 
192.29150000000001, 192.29150000000001, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 
192.53299999999999, 192.53299999999999, 192.53299999999999, 192.77474999999998, 192.77474999999998, 192.77474999999998, 
193.01650000000001, 193.01650000000001, 193.25825, 193.25825, 193.25825, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 
193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.74175, 193.74175, 193.98349999999999, 193.98349999999999, 
194.22524999999999, 194.22524999999999, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 
194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 
194.70850000000002, 194.70850000000002, 194.94999999999999, 194.94999999999999, 195.19149999999999, 195.19149999999999, 
195.19149999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 
195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 
195.67474999999999, 195.67474999999999, 195.91649999999998, 195.91649999999998, 195.91649999999998, 196.15824999999998, 
196.15824999999998, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 
196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 
196.40000000000001, 196.64175, 196.64175, 196.8835, 196.8835, 196.8835, 196.8835, 196.8835, 196.8835, 196.8835, 196.8835, 
196.8835, 196.8835, 196.8835, 196.8835, 196.8835, 196.8835, 197.12524999999999, 197.12524999999999, 197.12524999999999, 
197.12524999999999, 197.12524999999999, 197.12524999999999, 197.12524999999999, 197.36699999999999, 197.36699999999999, 
197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 
197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 
197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 
197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 
197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 
197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 
197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.12524999999999, 197.12524999999999, 
197.12524999999999, 197.12524999999999, 197.12524999999999, 196.8835, 196.8835, 196.64175, 196.64175, 196.64175, 196.64175, 
196.64175, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 
196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 
196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 
196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 
196.15825000000001, 196.15825000000001, 196.15825000000001, 195.91649999999998, 195.91649999999998, 195.67474999999999, 
195.67474999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 
195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 
195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 
195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.19149999999999, 195.19149999999999, 
195.19149999999999, 194.94999999999999, 194.94999999999999, 194.70849999999999, 194.70849999999999, 194.46700000000001, 
194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 
194.46700000000001, 194.46700000000001, 194.46700000000001, 194.22525000000002, 194.22525000000002, 193.98349999999999, 
193.98349999999999, 193.74175, 193.74175, 193.74175, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 
193.5, 193.5, 193.5, 193.5, 193.25825, 193.25825, 193.01650000000001, 193.01650000000001, 192.77475000000001, 192.77475000000001, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.29149999999998, 192.29149999999998, 192.29149999999998, 192.05000000000001, 192.05000000000001, 191.80850000000001, 191.80850000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.32525000000001, 191.32525000000001, 191.08350000000002, 191.08350000000002, 190.84175000000002, 190.84175000000002, 190.84175000000002, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.35825, 190.35825, 190.1165, 190.1165, 190.1165, 189.87475000000001, 189.87475000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.39150000000001, 189.39150000000001, 189.39150000000001, 189.39150000000001, 189.15000000000001, 189.15000000000001, 189.15000000000001, 188.9085, 188.9085, 188.9085, 188.9085, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.9085, 188.9085, 188.9085, 188.9085, 189.15000000000001, 189.15000000000001, 189.15000000000001, 189.39150000000001, 189.39150000000001, 189.39150000000001, 189.39150000000001, 189.39150000000001, 189.63300000000001, 189.63300000000001, 189.39150000000001, 189.39150000000001, 189.39150000000001, 189.39150000000001, 189.39150000000001, 189.39150000000001, 189.39150000000001, 189.39150000000001, 189.39150000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.87475000000001, 189.87475000000001, 190.1165, 190.1165, 190.35825, 190.35825, 190.35825, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.84174999999999, 190.84174999999999, 191.08350000000002, 191.08350000000002, 191.32525000000001, 191.32525000000001, 191.32525000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.80850000000001, 191.80850000000001, 192.05000000000001, 192.05000000000001, 192.05000000000001, 192.29150000000001, 192.29150000000001, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.77474999999998, 192.77474999999998, 192.77474999999998, 193.01650000000001, 193.01650000000001, 193.25825, 193.25825, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.74175, 193.74175, 193.98349999999999, 193.98349999999999, 194.22524999999999, 194.22524999999999, 194.22524999999999, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.70850000000002, 194.70850000000002, 194.94999999999999, 194.94999999999999, 194.94999999999999, 195.19149999999999, 195.19149999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.67474999999999, 195.67474999999999, 195.67474999999999, 195.91649999999998, 195.91649999999998, 196.15824999999998, 196.15824999999998, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.64175, 196.64175, 196.64175, 196.64175, 196.64175, 196.8835, 196.8835, 197.12524999999999, 197.12524999999999, 197.12524999999999, 197.12524999999999, 197.12524999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.12524999999999, 197.12524999999999, 196.8835, 196.8835, 196.64175, 196.64175, 196.64175, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.15825000000001, 196.15825000000001, 195.91649999999998, 195.91649999999998, 195.91649999999998, 195.67474999999999, 195.67474999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.19149999999999, 195.19149999999999, 194.94999999999999, 194.94999999999999, 194.70849999999999, 194.70849999999999, 194.70849999999999, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.22525000000002, 194.22525000000002, 193.98349999999999, 193.98349999999999, 193.74175, 193.74175, 193.74175, 193.5, 193.5,193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.25825, 193.25825, 193.01650000000001, 193.01650000000001, 193.01650000000001, 192.77475000000001, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.29149999999998, 192.29149999999998, 192.05000000000001, 192.05000000000001, 192.05000000000001, 191.80850000000001, 191.80850000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.32525000000001, 191.32525000000001, 191.32525000000001, 191.08350000000002, 191.08350000000002, 190.84175000000002, 190.84175000000002, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.35825, 190.35825, 190.35825, 190.1165, 190.1165, 189.87475000000001, 189.87475000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.39150000000001, 189.39150000000001, 189.39150000000001, 189.39150000000001, 189.39150000000001, 189.15000000000001, 189.15000000000001, 188.9085, 188.9085, 188.9085, 188.9085, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.667, 188.9085, 188.9085, 188.9085, 
189.15000000000001, 189.15000000000001, 189.39150000000001, 189.39150000000001, 189.63300000000001, 189.63300000000001, 
189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 
189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 
189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 
189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 189.63300000000001, 
189.63300000000001, 189.63300000000001, 189.87475000000001, 189.87475000000001, 189.87475000000001, 190.1165, 190.1165, 
190.35825, 190.35825, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 
190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 190.59999999999999, 
190.59999999999999, 190.59999999999999, 190.59999999999999, 190.84174999999999, 190.84174999999999, 190.84174999999999, 
191.08350000000002, 191.08350000000002, 191.32525000000001, 191.32525000000001, 191.56700000000001, 191.56700000000001, 
191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 
191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 191.56700000000001, 
191.80850000000001, 191.80850000000001, 191.80850000000001, 192.05000000000001, 192.05000000000001, 192.29150000000001, 
192.29150000000001, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 192.53299999999999, 
192.53299999999999, 192.53299999999999, 192.77474999999998, 192.77474999999998, 192.77474999999998, 193.01650000000001, 
193.01650000000001, 193.25825, 193.25825, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 
193.5, 193.5, 193.5, 193.74175, 193.74175, 193.74175, 193.98349999999999, 193.98349999999999, 194.22524999999999, 
194.22524999999999, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 
194.46700000000001, 194.46700000000001, 194.46700000000001, 194.70850000000002, 194.70850000000002, 194.94999999999999, 
194.94999999999999, 195.19149999999999, 195.19149999999999, 195.19149999999999, 195.43299999999999, 195.43299999999999,
 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 
195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.67474999999999, 
195.67474999999999, 195.67474999999999, 195.91649999999998, 195.91649999999998, 196.15824999999998, 196.15824999999998, 
196.15824999999998, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 
196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.64175, 196.64175, 196.64175, 196.64175, 196.64175, 196.8835, 196.8835, 197.12524999999999, 197.12524999999999, 197.12524999999999, 197.12524999999999, 197.12524999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 
197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.36699999999999, 197.12524999999999, 
197.12524999999999, 196.8835, 196.8835, 196.8835, 196.64175, 196.64175, 196.40000000000001, 196.40000000000001, 196.64175, 
196.64175, 196.64175, 196.64175, 196.64175, 196.64175, 196.64175, 196.64175, 196.64175, 196.64175, 196.40000000000001, 
196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.40000000000001, 196.15825000000001, 196.15825000000001, 195.91649999999998, 195.91649999999998, 195.67474999999999, 195.67474999999999, 195.67474999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.43299999999999, 195.19149999999999, 195.19149999999999, 195.19149999999999, 195.19149999999999, 194.94999999999999, 194.94999999999999, 194.94999999999999, 194.70849999999999, 194.70849999999999, 194.70849999999999, 194.70849999999999, 194.70849999999999, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.46700000000001, 194.22525000000002, 194.22525000000002, 193.98349999999999, 193.98349999999999, 193.74175, 193.74175, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.5, 193.25825, 193.25825, 193.25825, 193.01650000000001, 193.01650000000001])


    cooling_data = np.array([106.5000,  106.5000,  105.5330,  105.5330,  104.5670,  104.5670,  104.5670,  103.6000,  103.6000,  102.6330,  102.6330,  101.6670,  101.6670,  100.7000,  100.7000,   99.7333,   99.7333,   98.7667,   98.7667,   97.8000,   97.8000,   96.8333,   95.8667,   95.8667,   94.9000,   94.9000,   93.9333,   93.9333,   92.9667,   92.9667,   92.0000,   92.0000,   91.0333,   91.0333,   91.0333,   90.0667,   90.0667,   89.1000,   89.1000,   88.1333,   88.1333,   88.1333,   87.1667,   87.1667,   86.2000,   86.2000,   86.2000,   85.2333,   85.2333,   84.2667,   84.2667,   83.3000,   83.3000,   83.3000,   82.3333,   82.3333,   82.3333,   81.3667,   81.3667,   80.4000,   80.4000,   80.4000,   79.4333,   79.4333,   79.4333,   78.4667,   78.4667,   77.5000,   77.5000,   77.5000,   77.5000,   76.5333,   76.5333,   75.5667,   75.5667,   75.5667,   74.6000,   74.6000,   74.6000,   74.6000,   73.6333,   73.6333,   73.6333,   72.6667,   72.6667,   72.6667,   71.7000,   71.7000,   71.7000,   71.7000,   70.7333,   70.7333,   70.7333,   69.7667,   69.7667,   69.7667,   69.7667,   68.8000,   68.8000,   68.8000,   67.8333,   67.8333,   67.8333,   67.8333,   66.8667,   66.8667,   66.8667,   66.8667,   65.9000,   65.9000,   65.9000,   65.9000,   64.9333,   64.9333,   64.9333,   63.9667,   63.9667,   63.9667,   63.9667,   63.9667,   63.0000,   63.0000,   63.0000,   63.0000,   62.0333,   62.0333,   62.0333,   62.0333,   61.0667,   61.0667,   61.0667,   61.0667,   60.1000,   60.1000,   60.1000,   60.1000,   60.1000,   59.1333])

    class MyClass:
        def __init__(self):
            self.sleep = 0.1

    tune = Autotune(MyClass())
    tune.temps = data
    #tune.plot2(cooling_data)
    
    times = np.arange(0, len(cooling_data))
    z = np.polyfit(times, cooling_data, 2)
    p = np.poly1d(z)
    p2 = np.polyder(p)
    fit = p(times)
    fit2 = p2(times)
    #tune.plot2(fit)
    #tune.plot2(fit2)
    print("Heat loss: "+str(p2(0)))


    _ = plt.plot(times, cooling_data, '.', times, fit, '-', times, fit2, '--')
    plt.show()
    
    #print()
    #print(tune.get_periods())
    peaks = tune.detect_peaks(data)
    data = tune.smooth(data)
    peaks = tune.detect_peaks(data, show=True)
    valleys = tune.detect_peaks(data, valley=True, show=True)
    tune.calculate_PID(data, peaks, valleys)
    print(tune.Kp)
    print(tune.Ki)
    print(tune.Kd)






