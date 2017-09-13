"""
Util functions for Redeem

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


class Util:

    @staticmethod
    def smooth(x, window_len=100, window='hanning'):
        """
        smooth the data using a window with requested size.

        This method is based on the convolution of a scaled window with the
        signal. The signal is prepared by introducing reflected copies of the
        signal (with the window size) in both ends so that transient parts are
        minimized in the begining and end part of the output signal.

        Note: this function was taken from the SciPy cookbook:
        http://wiki.scipy.org/Cookbook/SignalSmooth

        """

        if x.size < window_len:
            raise ValueError("Input vector should be bigger than window size.")

        if window_len < 3:
            return x

        supported_window = ['flat',
                            'hanning',
                            'hamming',
                            'bartlett',
                            'blackman']

        if window not in supported_window:
            raise ValueError("Window is one of {}".format(supported_window))

        s = np.r_[x[window_len - 1:0:-1], x, x[-1:-window_len:-1]]
        # print(len(s))
        if window == 'flat':  # moving average
            w = np.ones(window_len, 'd')
        else:
            w = eval('np.' + window + '(window_len)')

        y = np.convolve(w / w.sum(), s, mode='valid')
        return y

    @staticmethod
    def detect_peaks(x, mph=None, mpd=1, threshold=0, edge='rising',
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
            detect peaks that are at least separated by minimum peak distance
            (in number of data).
        threshold : positive number, optional (default = 0)
            detect peaks (valleys) that are greater (smaller) than `threshold`
            in relation to their immediate neighbors.
        edge : {None, 'rising', 'falling', 'both'}, optional (default: rising)
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
        The detection of valleys instead of peaks is performed internally by
        simply negating the data: `ind_valleys = detect_peaks(-x)`

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
            ine = np.where((np.hstack((dx, 0)) < 0)
                           & (np.hstack((0, dx)) > 0))[0]
        else:
            if edge.lower() in ['rising', 'both']:
                ire = np.where((np.hstack((dx, 0)) <= 0)
                               & (np.hstack((0, dx)) > 0))[0]

            if edge.lower() in ['falling', 'both']:
                ife = np.where((np.hstack((dx, 0)) < 0)
                               & (np.hstack((0, dx)) >= 0))[0]

        ind = np.unique(np.hstack((ine, ire, ife)))
        # handle NaN's
        if ind.size and indnan.size:
            # NaN's and values close to NaN's cannot be peaks
            ind = ind[np.in1d(ind,
                              np.unique(np.hstack((indnan,
                                                   indnan - 1,
                                                   indnan + 1))),
                              invert=True)]
        # first and last values of x cannot be peaks
        if ind.size and ind[0] == 0:
            ind = ind[1:]
        if ind.size and ind[-1] == x.size - 1:
            ind = ind[:-1]
        # remove peaks < minimum peak height
        if ind.size and mph is not None:
            ind = ind[x[ind] >= mph]
        # remove peaks - neighbors < threshold
        if ind.size and threshold > 0:
            dx = np.min(np.vstack([x[ind] - x[ind - 1], x[ind] - x[ind + 1]]),
                        axis=0)
            ind = np.delete(ind, np.where(dx < threshold)[0])
        # detect small peaks closer than minimum peak distance
        if ind.size and mpd > 1:
            ind = ind[np.argsort(x[ind])][::-1]  # sort ind by peak height
            idel = np.zeros(ind.size, dtype=bool)
            for i in range(ind.size):
                if not idel[i]:
                    # keep peaks with the same height if kpsh is True
                    idel = idel | (ind >= ind[i] - mpd) \
                        & (ind <= ind[i] + mpd) \
                        & (x[ind[i]] > x[ind] if kpsh else True)
                    idel[i] = 0  # Keep current peak
            # remove the small peaks and sort back indices by their occurrence
            ind = np.sort(ind[~idel])

        if show:
            if indnan.size:
                x[indnan] = np.nan
            if valley:
                x = -x
            Util._plot(x, mph, mpd, threshold, edge, valley, ax, ind)

        return ind

    @staticmethod
    def _plot(x, mph, mpd, threshold, edge, valley, ax, ind):
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
            ax.set_xlim(-.02 * x.size, x.size * 1.02 - 1)
            ymin, ymax = x[np.isfinite(x)].min(), x[np.isfinite(x)].max()
            yrange = ymax - ymin if ymax > ymin else 1
            ax.set_ylim(ymin - 0.1 * yrange, ymax + 0.1 * yrange)
            ax.set_xlabel('Data #', fontsize=14)
            ax.set_ylabel('Amplitude', fontsize=14)
            mode = 'Valley detection' if valley else 'Peak detection'
            ax.set_title("%s (mph=%s, mpd=%d, threshold=%s, edge='%s')"
                         % (mode, str(mph), mpd, str(threshold), edge))
            # plt.grid()
            plt.show()
