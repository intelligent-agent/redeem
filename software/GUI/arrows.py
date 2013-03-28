import random
import wx
 
########################################################################
class TabPanel(wx.Panel):
    #----------------------------------------------------------------------
    def __init__(self, parent):
        """"""
        wx.Panel.__init__(self, parent=parent)
 
        #colors = ["red", "blue", "gray", "yellow", "green"]
        #self.SetBackgroundColour(random.choice(colors))
        
        
        imageLeft = wx.Image("arrow-left.jpg", wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        imageRight = wx.Image("arrow-right.jpg", wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        imageUp = wx.Image("arrow-up.jpg", wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        imageDown = wx.Image("arrow-down.jpg", wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        
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
        print "G91"
        print "G1 X-100 F4000"
        print "G90"

    def btnRightClick(self,event):
        print "G91"
        print "G1 X100 F4000"
        print "G90"

    def btnForwClick(self,event):
        print "G91"
        print "G1 Y100 F4000"
        print "G90"

    def btnBackClick(self,event):
        print "G91"
        print "G1 Y-100 F4000"
        print "G90"
    
    def btnUpClick(self,event):
        print "G91"
        print "G1 Z10 F4000"
        print "G90"

    def btnDownClick(self,event):
        print "G91"
        print "G1 Z-10 F4000"
        print "G90"      

 
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
if __name__ == "__main__":
    app = wx.App(False)
    frame = DemoFrame()
    frame.ShowFullScreen(True, style=wx.FULLSCREEN_ALL)
    app.MainLoop()
