#!/usr/bin/python

from __future__ import division
import matplotlib
matplotlib.use('TkAgg')

from multiprocessing import Process
from threading import Thread

from Tkinter import *
import argparse
import pylab as py
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import pickle
import numpy as np
from math import *
import time

image_x = 100
image_z = 80

class App:
    '''    
    Init
    '''
    def __init__(self, master):


        # Options            
        self.options = pickle.load(open("options.txt", "r+"))

        self.pins_P9 = list()
        self.pins_P8 = list()

        for i in range(23):
            self.pins_P9.append([IntVar(), IntVar()])
            self.pins_P8.append([IntVar(), IntVar()])
            
        # Master frame 
        master.title("BeagleBone pin mux util")
        frame = Frame(master)
        frame.pack()

        # The two things
        P9 = Frame(frame)        
        P8 = Frame(frame)        
 
        Label(P9, text="P9").pack(side=LEFT)
        P9.pack(side=TOP)
        for i in range(23):
            P9_line = Frame(P9)
            Checkbutton(P9_line, variable = self.pins_P9[i][0], onvalue = 1, offvalue = 0).pack(side=LEFT)
            Checkbutton(P9_line, variable = self.pins_P9[i][1], onvalue = 1, offvalue = 0).pack(side=LEFT)
            P9_line.pack(side=TOP)
        P9_line.pack(side=LEFT)

        Label(P8, text="P8").pack(side=LEFT)
        P8.pack(side=TOP)
        for i in range(23):
            P8 = Frame(frame)
            Checkbutton(P8, variable = self.pins_P8[i][0], onvalue = 1, offvalue = 0).pack(side=LEFT)
            Checkbutton(P8, variable = self.pins_P8[i][1], onvalue = 1, offvalue = 0).pack(side=LEFT)
            P8.pack(side=TOP)
        frame.pack(side=LEFT)

       
        self.status = Label(frame, text ="Statusbar")
        self.status.pack(side=LEFT)

       
    # Update the status
    def setStatus(self, stat):
        self.status.config(text = stat)

    # save the options
    def saveOptions(self):	
        pickle.dump(self.options, open("options.txt", "r+"))

root = Tk()
app = App(root)
root.mainloop()


