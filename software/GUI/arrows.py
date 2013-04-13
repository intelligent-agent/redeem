#!/usr/bin/env python
'''
A GUI for Hipsterbot

Author: Oyvind Nydal Dahl
email: oyvdahl@online.no
Website: http://www.build-electronic-circuits.com
License: BSD

You can use and change this, but keep this heading :)
'''

import random
import wx
import os, stat


#Named pipes for communicating with main 3d-printer controller
wfPath = "/var/tmp/rcape_in"
rfPath = "/var/tmp/rcape_out"



########################################################################
class TabPanel(wx.Panel):
    #----------------------------------------------------------------------
    def __init__(self, parent):
        """"""
        wx.Panel.__init__(self, parent=parent)
        dirname = "/home/ubuntu/replicape/software/GUI"
        
        imageLeft   = wx.Image(dirname+"/arrow-left.jpg",  wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        imageRight  = wx.Image(dirname+"/arrow-right.jpg", wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        imageUp     = wx.Image(dirname+"/arrow-up.jpg", 	  wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        imageDown   = wx.Image(dirname+"/arrow-down.jpg",  wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        
        btnLeft = wx.BitmapButton(self, id=-1, bitmap=imageLeft, pos=(10, 20), size = (imageLeft.GetWidth()+5, imageLeft.GetHeight()+5))
        btnRight = wx.BitmapButton(self, id=-1, bitmap=imageRight, pos=(10, 20), size = (imageRight.GetWidth()+5, imageRight.GetHeight()+5))
        btnForw = wx.BitmapButton(self, id=-1, bitmap=imageUp, pos=(10, 20), size = (imageUp.GetWidth()+5, imageUp.GetHeight()+5))
        btnBack = wx.BitmapButton(self, id=-1, bitmap=imageDown, pos=(10, 20), size = (imageDown.GetWidth()+5, imageDown.GetHeight()+5))
        btnUp = wx.BitmapButton(self, id=-1, bitmap=imageUp, pos=(10, 20), size = (imageUp.GetWidth()+5, imageUp.GetHeight()+5))
        btnDown = wx.BitmapButton(self, id=-1, bitmap=imageDown, pos=(10, 20), size = (imageDown.GetWidth()+5, imageDown.GetHeight()+5))
                
        #btnLeft = wx.Button(self, label="Left")
        #btnRight = wx.Button(self, label="Right")
        #btnForw = wx.Button(self, label="Forward")
        #btnBack = wx.Button(self, label="Backward")
        #btnUp = wx.Button(self, label="Up")
        #btnDown = wx.Button(self, label="Down")

        #Add click events to buttons
        btnLeft.Bind(wx.EVT_BUTTON, self.btnLeftClick)
        btnRight.Bind(wx.EVT_BUTTON, self.btnRightClick)
        btnForw.Bind(wx.EVT_BUTTON, self.btnForwClick)
        btnBack.Bind(wx.EVT_BUTTON, self.btnBackClick)
        btnUp.Bind(wx.EVT_BUTTON, self.btnUpClick)
        btnDown.Bind(wx.EVT_BUTTON, self.btnDownClick)
        
        #Create sizer
        sizer = wx.GridSizer(3,4)

        #Add buttons to sizer
        sizer.Add(btnUp, 0, wx.ALL, 10)
        sizer.Add(wx.Size(10,10)) #Empty space
        sizer.Add(btnForw, 0, wx.ALL, 10)
        sizer.Add(wx.Size(10,10)) #Empty space

        sizer.Add(wx.Size(10,10)) #Empty space
        sizer.Add(btnLeft, 0, wx.ALL, 10)
        sizer.Add(wx.Size(10,10)) #Empty space
        sizer.Add(btnRight, 0, wx.ALL, 10)

        sizer.Add(btnDown, 0, wx.ALL, 10)
        sizer.Add(wx.Size(10,10)) #Empty space
        sizer.Add(btnBack, 0, wx.ALL, 10)
        sizer.Add(wx.Size(10,10)) #Empty space

        self.SetSizer(sizer)


    #Button click events
    def btnLeftClick(self,event):
        write_to_pipe("G91")
        print "RX: " + read_from_pipe()
        write_to_pipe("G1 X-100 F4000")
        print "RX: " + read_from_pipe()
        write_to_pipe("G90")
        print "RX: " + read_from_pipe()

    def btnRightClick(self,event):
        write_to_pipe("G91")
        print "RX: " + read_from_pipe()
        write_to_pipe("G1 X100 F4000")
        print "RX: " + read_from_pipe()
        write_to_pipe("G90")
        print "RX: " + read_from_pipe()

    def btnForwClick(self,event):
        write_to_pipe("G91")
        print "RX: " + read_from_pipe()
        write_to_pipe("G1 Y100 F4000")
        print "RX: " + read_from_pipe()
        write_to_pipe("G90")
        print "RX: " + read_from_pipe()

    def btnBackClick(self,event):
        write_to_pipe("G91")
        print "RX: " + read_from_pipe()
        write_to_pipe("G1 Y-100 F4000")
        print "RX: " + read_from_pipe()
        write_to_pipe("G90")
        print "RX: " + read_from_pipe()
    
    def btnUpClick(self,event):
        write_to_pipe("G91")
        print "RX: " + read_from_pipe()
        write_to_pipe("G1 Z10 F4000")
        print "RX: " + read_from_pipe()
        write_to_pipe("G90")
        print "RX: " + read_from_pipe()

    def btnDownClick(self,event):
        write_to_pipe("G91")
        print "RX: " + read_from_pipe()
        write_to_pipe("G1 Z-10 F4000")
        print "RX: " + read_from_pipe()
        write_to_pipe("G90")
        print "RX: " + read_from_pipe()

 
########################################################################
class DemoFrame(wx.Frame):
    """
    Frame that holds all other widgets
    """
 
    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""        
	wx.Frame.__init__(self, None, wx.ID_ANY, 'Full display size', pos=(0, 0), size=wx.DisplaySize())
        panel = wx.Panel(self)
 
        notebook = wx.Notebook(panel)
        tabOne = TabPanel(notebook)
        notebook.AddPage(tabOne, "Tab 1")
 
        #tabTwo = TabPanel(notebook)
        #notebook.AddPage(tabTwo, "Tab 2")
 
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(notebook, 1, wx.ALL|wx.EXPAND, 5)
        panel.SetSizer(sizer)
        self.Layout()
 
        self.Show()
 
    #----------------------------------------------------------------------



###########################################################################
def check_com():
    #Check if named pipes exist, exit if not
    try:
        if not stat.S_ISFIFO(os.stat(wfPath).st_mode):
            print "Communication error with " + wfPath
            exit(1)

        if not stat.S_ISFIFO(os.stat(rfPath).st_mode):
            print "Communication error with " + rfPath
            exit(1)

    except OSError:
        print "Communication error"
        exit(1)

###########################################################################
def write_to_pipe(msg):
    wp = open(wfPath, 'w')
    wp.write(msg + "\n")		
    wp.close()
    print "TX: " + msg


###########################################################################
def read_from_pipe():
    rp = open(rfPath, 'r')
    message = ""
    messages = rp.readlines()
    for msg in messages:
        message = message + msg
    rp.close()
    
    return message

###########################################################################    
if __name__ == "__main__":
    check_com()
    app = wx.App(False)
    frame = DemoFrame()
    frame.ShowFullScreen(True, style=wx.FULLSCREEN_ALL)
    app.MainLoop()
