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
from threading import Thread
import time
import logging
import numpy as np


class Autotune:

    def __init__(self, heater, temp=100.0, cycles=3):        
        self.heater = heater
        self.noise_band = 0.5
        # Steady state starting temperture
        self.steady_temperature = temp
        self.cycles = cycles
        # Degrees to step
        self.output_step = 10.0
        self.stable_start_seconds = 10
        self.sleep = 0.1
        
    def cancel(self):
        self.running = False
        self.t.join()

    def run(self):
        """ Start the PID autotune loop """
        # Reset found peaks
        self.running = True
        self.temps = []
        
        # Wait for temperature to stabilize
        self.heater.set_target_temperature(self.steady_temperature)
        while not self.heater.is_temperature_stable(self.stable_start_seconds):
            time.sleep(1)

        # Set the standard parameters
        self.old_ok_range = self.heater.ok_range
        self.heater.P = 0.5
        self.heater.I = 0.0
        self.heater.D = 0.0
        self.heater.ok_range = 0.5

        self.d = self.bias = 0.5

        # Start stepping temperatures
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
        self.heater.set_target_temperature(self.steady_temperature)

    def _tune(self):
        for peak in range(self.cycles):
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

            if peak == 0:
                self.temps = []
                continue
            if peak >= 2:
                smooth = self.smooth(np.array(self.temps))
                peaks = self.detect_peaks(smooth)
                diff = np.diff(smooth[peaks[-2:]])
                logging.debug("Difference between last two peaks: "+str(diff)+" deg. C.")
                print("Difference between last two peaks: "+str(diff)+" deg. C.")

                # TODO: Adjust Power based on diff. 
                #self.heater.P = ??
                logging.debug("Setting heater P: "+str(self.heater.P))
                            
    def calculate_PID(self, temps, peaks, valleys):
        abs_max = temps[peaks[-1]]
        abs_min = temps[valleys[-1]]

        logging.debug("Temperature Gain: "+str(abs_max-abs_min)+" deg. C")
        print("Gain: "+str(abs_max-abs_min))

        # Calculate the oscillation period of the peaks
        Pu = (peaks[-1]-peaks[-2])*self.heater.sleep
        # Calculate the ultimate gain 
        Ku = 4.0*self.output_step/(np.pi*(abs_max-abs_min)/2.0)

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


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    data = np.array([99.5, 99.400000000000006, 99.299999999999997, 99.200000000000003, 99.200000000000003, 99.099999999999994, 99.099999999999994, 99.099999999999994, 99.099999999999994, 99.099999999999994, 99.099999999999994, 99.099999999999994, 99.099999999999994, 99.0, 98.900000000000006, 98.900000000000006, 99.0, 99.0, 99.0, 98.900000000000006, 99.0, 99.0, 99.099999999999994, 99.200000000000003, 99.400000000000006, 99.599999999999994, 99.599999999999994, 99.799999999999997, 99.799999999999997, 99.900000000000006, 100.09999999999999, 100.09999999999999, 100.3, 100.40000000000001, 100.59999999999999, 100.8, 100.8, 101.0, 101.09999999999999, 101.3, 101.5, 101.7, 102.0, 102.2, 102.2, 102.5, 102.59999999999999, 102.8, 103.0, 103.2, 103.40000000000001, 103.40000000000001, 103.7, 103.90000000000001, 104.09999999999999, 104.3, 104.40000000000001, 104.59999999999999, 104.8, 104.8, 104.90000000000001, 105.0, 105.2, 105.2, 105.2, 105.3, 105.3, 105.5, 105.7, 105.8, 105.90000000000001, 106.09999999999999, 106.2, 106.40000000000001, 106.59999999999999, 106.59999999999999, 106.8, 107.0, 107.0, 107.09999999999999, 107.3, 107.3, 107.3, 107.3, 107.40000000000001, 107.3, 107.40000000000001, 107.40000000000001, 107.3, 107.40000000000001, 107.40000000000001, 107.40000000000001, 107.40000000000001, 107.40000000000001, 107.5, 107.59999999999999, 107.59999999999999, 107.5, 107.5, 107.5, 107.5, 107.40000000000001, 107.3, 107.3, 107.40000000000001, 107.40000000000001, 107.40000000000001, 107.40000000000001, 107.40000000000001, 107.40000000000001, 107.40000000000001, 107.40000000000001, 107.5, 107.5, 107.5, 107.40000000000001, 107.40000000000001, 107.3, 107.40000000000001, 107.40000000000001, 107.5, 107.5, 107.5, 107.40000000000001, 107.40000000000001, 107.40000000000001, 107.40000000000001, 107.40000000000001, 107.40000000000001, 107.3, 107.40000000000001, 107.3, 107.3, 107.3, 107.40000000000001, 107.3, 107.40000000000001, 107.40000000000001, 107.40000000000001, 107.40000000000001, 107.40000000000001, 107.2,107.2, 107.2, 107.2, 107.2, 107.2, 107.09999999999999, 107.0, 107.0, 107.0, 107.0, 107.0, 107.09999999999999, 107.0, 107.0, 106.90000000000001, 106.90000000000001, 106.90000000000001, 106.90000000000001, 106.8, 106.7, 106.90000000000001, 106.7, 106.7, 106.59999999999999, 106.59999999999999, 106.59999999999999, 106.5, 106.40000000000001, 106.3, 106.3, 106.3, 106.09999999999999, 106.09999999999999, 106.09999999999999, 106.09999999999999, 105.90000000000001, 105.8, 105.8, 105.7, 105.7, 105.59999999999999, 105.59999999999999, 105.59999999999999, 105.5, 105.40000000000001, 105.40000000000001, 105.40000000000001, 105.40000000000001, 105.3, 105.3, 105.3, 105.2, 105.09999999999999, 105.09999999999999, 105.09999999999999, 105.0, 105.0, 105.0, 105.0, 105.0, 105.0, 105.0, 104.90000000000001, 104.90000000000001, 104.90000000000001, 104.8, 104.8, 104.7, 104.59999999999999, 104.59999999999999, 104.59999999999999, 104.5, 104.5, 104.5, 104.5, 104.5, 104.59999999999999, 104.59999999999999, 104.59999999999999, 104.59999999999999, 104.5, 104.40000000000001, 104.40000000000001, 104.40000000000001, 104.3, 104.2, 104.09999999999999, 104.0, 104.0, 104.0, 104.0, 104.0, 104.0, 104.0, 104.0, 103.90000000000001, 103.90000000000001, 103.90000000000001, 103.90000000000001, 103.8, 103.8, 103.8, 103.8, 103.8, 103.7, 103.8, 103.7, 103.59999999999999, 103.59999999999999, 103.59999999999999, 103.5, 103.5, 103.40000000000001, 103.40000000000001, 103.3, 103.3, 103.2, 103.2, 103.2, 103.09999999999999, 103.09999999999999, 103.09999999999999, 103.09999999999999, 103.0, 103.0, 103.0, 103.0, 103.0, 103.0, 103.0, 103.0, 103.0, 102.90000000000001, 102.8, 102.8, 102.8, 102.8, 102.8, 102.7, 102.59999999999999, 102.5, 102.5, 102.5, 102.5, 102.5, 102.40000000000001, 102.3, 102.2, 102.09999999999999, 102.09999999999999, 102.09999999999999, 102.09999999999999, 102.0, 102.0, 102.0, 102.0, 101.90000000000001, 101.90000000000001, 101.90000000000001, 101.90000000000001, 101.90000000000001, 101.8, 101.8, 101.8, 101.8, 101.8, 101.7, 101.8, 101.7, 101.7, 101.59999999999999, 101.59999999999999, 101.5, 101.5, 101.40000000000001, 101.3, 101.3, 101.3, 101.2, 101.2, 101.09999999999999, 101.09999999999999, 101.09999999999999, 101.09999999999999, 101.0, 101.0, 101.0, 101.0, 101.0, 101.0, 100.90000000000001, 100.90000000000001, 100.90000000000001, 100.90000000000001, 100.90000000000001, 100.8, 100.7, 100.7, 100.7, 100.59999999999999, 100.5, 100.59999999999999, 100.59999999999999, 100.59999999999999, 100.5, 100.3, 100.3, 100.40000000000001, 100.3, 100.3, 100.3, 100.3, 100.2, 100.09999999999999, 100.09999999999999, 100.0, 100.09999999999999, 100.09999999999999, 100.0, 100.0, 99.900000000000006, 99.900000000000006, 99.799999999999997, 99.799999999999997, 99.799999999999997, 99.900000000000006, 99.900000000000006, 99.900000000000006, 99.900000000000006, 99.900000000000006, 99.900000000000006, 99.900000000000006, 99.799999999999997, 99.799999999999997, 99.700000000000003, 99.599999999999994, 99.5, 99.5, 99.400000000000006, 99.299999999999997, 99.099999999999994, 99.099999999999994, 99.099999999999994, 99.0, 99.0, 99.099999999999994, 99.099999999999994, 99.099999999999994, 99.0, 99.0, 99.0, 99.099999999999994, 99.099999999999994, 99.099999999999994, 99.099999999999994, 99.099999999999994, 99.200000000000003, 99.200000000000003, 99.200000000000003, 99.299999999999997, 99.299999999999997, 99.400000000000006, 99.5, 99.599999999999994, 99.700000000000003, 99.799999999999997, 99.900000000000006, 99.900000000000006, 100.09999999999999, 100.3, 100.40000000000001, 100.5, 100.7, 100.8, 101.0, 101.2, 101.40000000000001, 101.7, 101.90000000000001, 102.09999999999999, 102.3, 102.5, 102.5, 102.7, 103.0, 103.2, 103.40000000000001, 103.40000000000001, 103.5, 103.7, 103.90000000000001, 104.09999999999999, 104.3, 104.40000000000001, 104.5, 104.59999999999999, 104.8, 104.8, 105.0, 105.2, 105.2, 105.2, 105.3, 105.5, 105.59999999999999, 105.7, 106.0, 106.09999999999999, 106.3, 106.5, 106.7, 106.90000000000001, 107.0, 107.0, 107.09999999999999, 107.3, 107.3, 107.2, 107.3, 107.40000000000001, 107.3, 107.3, 107.40000000000001, 107.40000000000001, 107.40000000000001, 107.5, 107.40000000000001, 107.40000000000001, 107.40000000000001, 107.3, 107.40000000000001, 107.5, 107.40000000000001, 107.40000000000001, 107.40000000000001, 107.5, 107.5, 107.5, 107.59999999999999, 107.59999999999999, 107.59999999999999, 107.5, 107.40000000000001, 107.5, 107.5, 107.5, 107.5, 107.5, 107.40000000000001, 107.40000000000001, 107.40000000000001, 107.40000000000001, 107.40000000000001, 107.40000000000001, 107.3, 107.40000000000001, 107.40000000000001, 107.3, 107.3, 107.3, 107.2, 107.2, 107.2, 107.3, 107.3, 107.3, 107.3, 107.2, 107.3, 107.40000000000001, 107.5, 107.5, 107.5, 107.59999999999999, 107.5, 107.59999999999999, 107.5, 107.59999999999999, 107.59999999999999, 107.5, 107.40000000000001, 107.40000000000001, 107.5, 107.5, 107.40000000000001, 107.40000000000001, 107.3, 107.40000000000001, 107.3, 107.3, 107.3, 107.3, 107.3, 107.2, 107.09999999999999, 107.09999999999999, 107.09999999999999, 106.90000000000001, 106.8, 106.59999999999999, 106.59999999999999, 106.5, 106.40000000000001, 106.3, 106.2, 106.2, 106.09999999999999, 106.0, 106.0, 105.90000000000001, 105.8, 105.7, 105.7, 105.59999999999999, 105.59999999999999, 105.59999999999999, 105.59999999999999, 105.59999999999999, 105.59999999999999, 105.59999999999999, 105.59999999999999, 105.7, 105.7, 105.7, 105.8, 105.7, 105.59999999999999, 105.5, 105.40000000000001, 105.3, 105.3, 105.3, 105.3, 105.2, 105.0, 105.0, 104.90000000000001, 104.90000000000001, 104.90000000000001, 104.8, 104.8, 104.8, 104.59999999999999, 104.59999999999999, 104.59999999999999, 104.7, 104.7, 104.8, 104.8, 104.8, 104.7, 104.59999999999999, 104.7, 104.7, 104.59999999999999, 104.5, 104.5, 104.40000000000001, 104.3, 104.3, 104.3, 104.3, 104.3, 104.2, 104.09999999999999, 104.09999999999999, 104.09999999999999, 104.09999999999999, 104.09999999999999, 104.09999999999999, 104.0, 104.0, 104.0, 104.0, 104.0, 104.0, 103.90000000000001, 103.90000000000001, 103.90000000000001, 103.90000000000001, 103.90000000000001, 103.90000000000001, 103.90000000000001, 103.90000000000001, 103.90000000000001, 103.90000000000001, 103.90000000000001, 104.0, 103.90000000000001, 103.8, 103.7, 103.7, 103.59999999999999, 103.5, 103.40000000000001, 103.3, 103.2, 103.09999999999999, 103.09999999999999, 103.09999999999999, 103.09999999999999, 103.09999999999999, 103.0, 103.0, 103.0, 103.0, 103.0, 102.90000000000001, 102.8, 102.8, 102.8, 102.8, 102.7, 102.7, 102.7, 102.7, 102.7, 102.7, 102.7, 102.7, 102.59999999999999, 102.59999999999999, 102.5, 102.5, 102.5, 102.40000000000001, 102.3, 102.2, 102.2, 102.09999999999999, 102.09999999999999, 102.09999999999999, 102.0, 102.0, 102.0, 101.8, 101.8, 101.8, 101.8, 101.8, 101.90000000000001, 101.90000000000001, 101.8, 101.8, 101.8, 101.8, 101.8, 101.7, 101.59999999999999, 101.5, 101.5, 101.40000000000001, 101.3, 101.40000000000001, 101.3, 101.09999999999999, 101.09999999999999, 101.09999999999999, 101.09999999999999, 101.09999999999999, 101.09999999999999, 101.09999999999999, 101.09999999999999, 101.09999999999999, 101.0, 101.0, 101.09999999999999, 101.09999999999999, 101.09999999999999, 101.0, 101.0, 101.0, 100.90000000000001, 100.8, 100.8, 100.8, 100.7, 100.7, 100.7, 100.7, 100.7, 100.7, 100.59999999999999, 100.59999999999999, 100.59999999999999, 100.59999999999999, 100.5, 100.40000000000001, 100.3, 100.2, 100.09999999999999, 100.0, 100.0, 99.900000000000006, 99.900000000000006, 99.799999999999997, 99.700000000000003, 99.700000000000003, 99.700000000000003, 99.799999999999997, 99.700000000000003, 99.700000000000003, 99.700000000000003, 99.700000000000003, 99.599999999999994, 99.599999999999994]
)

    data2 = np.array( [57.200000000000003, 58.166699999999999, 58.166699999999999, 58.166699999999999, 58.166699999999999, 58.166699999999999, 58.166699999999999, 58.166699999999999, 59.133299999999998, 59.133299999999998, 59.133299999999998, 60.100000000000001, 59.133299999999998, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 61.066699999999997, 61.066699999999997, 61.066699999999997, 61.066699999999997, 61.066699999999997, 61.066699999999997, 61.066699999999997, 61.066699999999997, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 59.133299999999998, 59.133299999999998, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 61.066699999999997, 61.066699999999997, 61.066699999999997, 61.066699999999997, 61.066699999999997, 61.066699999999997, 61.066699999999997, 61.066699999999997, 61.066699999999997, 61.066699999999997, 61.066699999999997, 61.066699999999997, 60.100000000000001, 61.066699999999997, 61.066699999999997, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 59.133299999999998, 59.133299999999998, 60.100000000000001, 59.133299999999998, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001, 60.100000000000001])

    class MyClass:
        def __init__(self):
            self.sleep = 0.1

    tune = Autotune(MyClass())
    tune.temps = data
    print()
    print(tune.get_periods())
    peaks = tune.detect_peaks(data, show=True)
    data = tune.smooth(data)
    peaks = tune.detect_peaks(data, show=True)
    valleys = tune.detect_peaks(data, valley=True, show=True)
    tune.calculate_PID(data, peaks, valleys)
    print(tune.Kp)
    print(tune.Ki)
    print(tune.Kd)


