
import wx
import wx.lib.buttons as buttons
import logger
#import wx.xrc



#helper function -------
def scale_bitmap(bitmap, width, height):
    image = wx.ImageFromBitmap(bitmap)
    image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
    result = wx.BitmapFromImage(image)
    return result



class AnalogOutPanel( wx.Panel ):
	def __init__(self, parent, name, idx):
		wx.Panel.__init__(self, parent)
		self.parent = parent

		self.onBitmap = scale_bitmap(wx.Bitmap("green-led-on-md.png"), 30, 30)
		self.offBitmap = scale_bitmap(wx.Bitmap("green-led-off-md.png"), 30, 30)
		self.recordOn = scale_bitmap(wx.Bitmap("record-button-on.png"), 25, 25)
		self.recordOff = scale_bitmap(wx.Bitmap("record-button-off.png"),25, 25)

		mainSizer = wx.BoxSizer(wx.VERTICAL)
		
		titleSizer = wx.BoxSizer(wx.HORIZONTAL)
		controlSizer = wx.BoxSizer(wx.HORIZONTAL)
		buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
	
		#create the title first
		lineLeft = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		self.channelName = wx.StaticText( self, wx.ID_ANY, name, wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
		self.channelName.Wrap( -1 )
		lineRight = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		self.recordBtn = buttons.GenBitmapToggleButton(self, id=wx.ID_ANY, bitmap=self.recordOff, size=(self.recordOff.GetWidth()+1, self.recordOff.GetHeight()+1))
		self.recordBtn.SetBitmapSelected(self.recordOn)
			# add everything to the title sizer
		titleSizer.Add( lineLeft, 1, wx.TOP|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5 )
		titleSizer.Add( self.channelName, 0, wx.ALIGN_CENTER_VERTICAL, 5 )
		titleSizer.Add( lineRight, 1, wx.TOP|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
		titleSizer.Add( self.recordBtn, 0, wx.LEFT|wx.BOTTOM|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5 )

		# create the channel controls
		self.outputPwrTxt = wx.StaticText(self, wx.ID_ANY, "Output Power (0-1000)   ", wx.DefaultPosition, wx.DefaultSize, 0 ) 
		self.outputPwr = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 100,-1 ), 0 )
		self.outputPwrUnit = wx.StaticText( self, wx.ID_ANY, " ", wx.DefaultPosition, wx.DefaultSize, 0 )
		#add everything to the control sizer
		controlSizer.Add( self.outputPwrTxt, 0, wx.TOP|wx.BOTTOM|wx.LEFT, 5 )
		controlSizer.Add( self.outputPwr, 0, wx.BOTTOM, 5 )
		controlSizer.Add( self.outputPwrUnit, 0, wx.ALL, 5 )

		# create the bottom start/stop buttons
		#self.startBtn = wx.ToggleButton( self, wx.ID_ANY, "On", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.startBtn = buttons.GenBitmapToggleButton(self, id=wx.ID_ANY, bitmap=self.offBitmap, size=(self.offBitmap.GetWidth()+5, self.offBitmap.GetHeight()+5))
		self.startBtn.SetBitmapSelected(self.onBitmap)
		self.runForBtn =  wx.Button( self, wx.ID_ANY, "Set Timer", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.progressBar = wx.Gauge( self, wx.ID_ANY, 100, wx.DefaultPosition, (5,5), wx.GA_HORIZONTAL )
		self.timer = wx.StaticText(self, wx.ID_ANY, "000:00:00", wx.DefaultPosition, wx.DefaultSize, 0 ) 
		self.timer.Enable(False)
			#add everything to the bottom sizer
		buttonSizer.Add( self.runForBtn, 0, wx.ALL, 5 )
		buttonSizer.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		buttonSizer.Add( self.timer, 0, wx.ALL, 10 )
		buttonSizer.Add( self.startBtn, 0, wx.ALL, 0 )

	

		# Add all three sizers
		mainSizer.Add( titleSizer, 0, wx.TOP|wx.EXPAND, 5 )
		mainSizer.Add(controlSizer, 0, wx.EXPAND, 5)
		mainSizer.Add(buttonSizer, 0, wx.EXPAND, 5)
		mainSizer.Add(self.progressBar, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 0)
	
		self.SetSizer(mainSizer)
		
# Panel with all the analog-input channel widgets in
class AnalogInPanel( wx.Panel ):
	def __init__(self, parent, name, idx):
		wx.Panel.__init__(self, parent)
		self.parent = parent
		
		self.onBitmap = scale_bitmap(wx.Bitmap("blue-led-on-md.png"), 30, 30)
		self.offBitmap = scale_bitmap(wx.Bitmap("blue-led-off-md.png"), 30, 30)
		self.recordOn = scale_bitmap(wx.Bitmap("record-button-on.png"), 25, 25)
		self.recordOff = scale_bitmap(wx.Bitmap("record-button-off.png"),25, 25)


		mainSizer = wx.BoxSizer(wx.VERTICAL)
		
		titleSizer = wx.BoxSizer(wx.HORIZONTAL)
		controlSizer = wx.BoxSizer(wx.HORIZONTAL)
		buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
	
		#create the title first
		lineLeft = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		self.channelName = wx.StaticText( self, wx.ID_ANY, name, wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
		self.channelName.Wrap( -1 )
		lineRight = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		self.recordBtn = buttons.GenBitmapToggleButton(self, id=wx.ID_ANY, bitmap=self.recordOff, size=(self.recordOff.GetWidth()+1, self.recordOff.GetHeight()+1))
		self.recordBtn.SetBitmapSelected(self.recordOn)
			# add everything to the title sizer
		titleSizer.Add( lineLeft, 1, wx.TOP|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5 )
		titleSizer.Add( self.channelName, 0, wx.ALIGN_CENTER_VERTICAL, 5 )
		titleSizer.Add( lineRight, 1, wx.TOP|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5 )
		titleSizer.Add( self.recordBtn, 0, wx.LEFT|wx.BOTTOM|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5 )

		# create the channel controls
		self.sampleRateTxt = wx.StaticText(self, wx.ID_ANY, "Sample Rate (/sec): ", wx.DefaultPosition, wx.DefaultSize, 0 ) 
		self.sampleRate = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 100,-1 ), 0 )
		#self.sampleRateUnit = wx.StaticText( self, wx.ID_ANY, "   1:05", wx.DefaultPosition, wx.DefaultSize, 0 )
		#self.outputFileTxt = wx.StaticText( self, wx.ID_ANY, "Output File:", wx.DefaultPosition, wx.DefaultSize, 0 )
		#self.outputFile = wx.StaticText( self, wx.ID_ANY, "None", wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
		#self.outputFilePicker = wx.FilePickerCtrl( self, wx.ID_ANY, wx.EmptyString, "Select a file", "*.*", wx.DefaultPosition, wx.DefaultSize, wx.FLP_SAVE )
		#add everything to the control sizer
		controlSizer.Add( self.sampleRateTxt, 0, wx.TOP|wx.BOTTOM|wx.LEFT, 5 )
		controlSizer.Add( self.sampleRate, 0, wx.BOTTOM, 5 )
		#controlSizer.Add( self.sampleRateUnit, 0, wx.ALL, 5 )
		#controlSizer.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )

		# create the bottom start/stop buttons
		self.startBtn = buttons.GenBitmapToggleButton(self, id=wx.ID_ANY, bitmap=self.offBitmap, size=(self.offBitmap.GetWidth()+5, self.offBitmap.GetHeight()+5))
		self.startBtn.SetBitmapSelected(self.onBitmap)
		self.runForBtn =  wx.Button( self, wx.ID_ANY, "Set Timer", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.timer = wx.StaticText(self, wx.ID_ANY, "000:00:00", wx.DefaultPosition, wx.DefaultSize, 0 ) 
		self.timer.Enable(False)
		self.progressBar = wx.Gauge( self, wx.ID_ANY, 100, wx.DefaultPosition, (5,5), wx.GA_HORIZONTAL )
		#add everything to the bottom sizer
		buttonSizer.Add( self.startBtn, 0, wx.ALL, 0 )
		#buttonSizer.Add( self.outputFilePicker, 0, wx.ALL, 5 )
		buttonSizer.Add( self.timer, 0, wx.ALL, 10 )
		buttonSizer.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		buttonSizer.Add( self.runForBtn, 0, wx.ALL, 5 )

	

		# Add all three sizers
		mainSizer.Add( titleSizer, 0, wx.TOP|wx.EXPAND, 5 )
		mainSizer.Add(controlSizer, 0, wx.EXPAND, 5)
		mainSizer.Add(buttonSizer, 0, wx.EXPAND, 5)
		mainSizer.Add(self.progressBar, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 0)
	
		self.SetSizer(mainSizer)
		
		
# Panel with all the digital channel widgets in
class DigitalPanel( wx.Panel ):
	def __init__(self, parent, name, idx, n):
		wx.Panel.__init__(self, parent)
		self.parent = parent
		self.lights = []
		self.switches = []
		self.labels = []

		self.onBitmap = scale_bitmap(wx.Bitmap("green-led-on-md.png"), 30, 30)
		self.offBitmap = scale_bitmap(wx.Bitmap("green-led-off-md.png"), 30, 30)
		self.onBitmap2 = scale_bitmap(wx.Bitmap("blue-led-on-md.png"), 30, 30)
		self.offBitmap2 = scale_bitmap(wx.Bitmap("blue-led-off-md.png"), 30, 30)
		self.recordOn = scale_bitmap(wx.Bitmap("record-button-on.png"), 25, 25)
		self.recordOff = scale_bitmap(wx.Bitmap("record-button-off.png"),25, 25)


		mainSizer = wx.BoxSizer(wx.VERTICAL)
		
		titleSizer = wx.BoxSizer(wx.HORIZONTAL)
		buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
		buttonSizerL = wx.BoxSizer(wx.VERTICAL)
		buttonSizerR = wx.BoxSizer(wx.VERTICAL)
	
		#create the title first
		lineLeft = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		self.channelName = wx.StaticText( self, wx.ID_ANY, name, wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
		self.channelName.Wrap( -1 )
		lineRight = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		self.recordBtn = buttons.GenBitmapToggleButton(self, id=wx.ID_ANY, bitmap=self.recordOff, size=(self.recordOff.GetWidth()+1, self.recordOff.GetHeight()+1))
		self.recordBtn.SetBitmapSelected(self.recordOn)
			# add everything to the title sizer
		titleSizer.Add( lineLeft, 1, wx.TOP|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5 )
		titleSizer.Add( self.channelName, 0, wx.ALIGN_CENTER_VERTICAL, 5 )
		titleSizer.Add( lineRight, 1, wx.TOP|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5 )
		titleSizer.Add( self.recordBtn, 0, wx.LEFT|wx.BOTTOM|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5 )

		# create the channel controls
		#self.sampleRateTxt = wx.StaticText(self, wx.ID_ANY, "Sample Rate: ", wx.DefaultPosition, wx.DefaultSize, 0 ) 
		#self.sampleRate = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 100,-1 ), 0 )
		#self.sampleRateUnit = wx.StaticText( self, wx.ID_ANY, "samples/sec", wx.DefaultPosition, wx.DefaultSize, 0 )
		#self.outputFileTxt = wx.StaticText( self, wx.ID_ANY, "Output File:", wx.DefaultPosition, wx.DefaultSize, 0 )
		#self.outputFile = wx.StaticText( self, wx.ID_ANY, "None", wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
		#self.outputFilePicker = wx.FilePickerCtrl( self, wx.ID_ANY, wx.EmptyString, "Select a file", "*.*", wx.DefaultPosition, wx.DefaultSize, wx.FLP_SAVE )
		#add everything to the control sizer
		#controlSizer.Add( self.sampleRateTxt, 0, wx.TOP|wx.BOTTOM|wx.LEFT, 5 )
		#controlSizer.Add( self.sampleRate, 0, wx.BOTTOM, 5 )
		#controlSizer.Add( self.sampleRateUnit, 0, wx.ALL, 5 )
		#controlSizer.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		#fileSizer.Add( self.outputFileTxt, 0, wx.TOP|wx.BOTTOM|wx.LEFT, 5 )
		#fileSizer.Add( self.outputFile, 0, wx.TOP|wx.BOTTOM|wx.RIGHT, 5 )
		#fileSizer.Add( self.outputFilePicker, 0, wx.ALL, 5 )

		# create the bottom start/stop buttons
		for x in range(n):
			newSizer = wx.BoxSizer(wx.HORIZONTAL)
			#newLight = wx.ToggleButton( self, wx.ID_ANY, "?", wx.DefaultPosition, wx.DefaultSize, 0 )
			#newSwitch = wx.ToggleButton( self, wx.ID_ANY, "dir", wx.DefaultPosition, wx.DefaultSize, 0 )
			newLight = buttons.GenBitmapToggleButton(self, id=wx.ID_ANY, bitmap=self.offBitmap2, size=(self.offBitmap.GetWidth()+5, self.offBitmap.GetHeight()+5))
			newLabel = wx.StaticText( self, wx.ID_ANY, "In/Out", wx.DefaultPosition, wx.Size( -1,-1 ), 0 ) 
			
			#newSwitch = buttons.GenBitmapToggleButton(self, id=wx.ID_ANY, bitmap=self.onBitmap, size=(self.onBitmap.GetWidth()+5, self.onBitmap.GetHeight()+5))
			#newSwitch.SetBitmapSelected(self.offBitmap)
			self.lights.append( newLight )
			self.labels.append( newLabel )
			#self.switches.append( newSwitch )
			#newSizer.Add( newLight )
			#newSizer.AddStretchSpacer()
			#newSizer.Add( newSwitch )
			if x>=n/2:
				newLight.SetBitmapSelected(self.onBitmap2)
				newLight.SetBitmapLabel(self.offBitmap2)
				newLabel.SetLabel("Input")
				newSizer.Add( newLight )
				newSizer.Add( newLabel )
				buttonSizerL.Add( newSizer, 0, wx.EXPAND, 30 )
			else:
				newLight.SetBitmapSelected(self.onBitmap)
				newLight.SetBitmapLabel(self.offBitmap)
				newLabel.SetLabel("Output")
				newSizer.AddStretchSpacer()
				newSizer.Add( newLabel )
				newSizer.Add( newLight )
				buttonSizerR.Add( newSizer, 0, wx.EXPAND, 30 )
		vline = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_VERTICAL ) 
	
		buttonSizer.Add(buttonSizerL, 1, wx.EXPAND, 0)
		buttonSizer.Add(vline, 0, wx.EXPAND|wx.ALL, 5)
		buttonSizer.Add(buttonSizerR, 1, wx.EXPAND, 0)

		# Add all three sizers
		mainSizer.Add( titleSizer, 0, wx.TOP|wx.EXPAND, 5 )
		mainSizer.Add(buttonSizer, 0, wx.EXPAND, 5)
	
		self.SetSizer(mainSizer)

    #----------------------------------------------------------------------
class TopPanel ( wx.Panel ):
	channels = dict()

	def __init__(self, parent):
		"""Constructor"""
		wx.Panel.__init__(self, parent)
		self.frame = parent
 
		self.mainSizer = wx.BoxSizer(wx.VERTICAL)
		topSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.channelSizer = wx.BoxSizer(wx.VERTICAL)

		# stuff at the top of the GUI
		topTxt = wx.StaticText( self, wx.ID_ANY, "Optical Fiber Systems", wx.DefaultPosition, wx.DefaultSize, 0 )
	
	
		topSizer.Add( topTxt, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )
 
        
 
		self.mainSizer.Add(topSizer, 1, wx.CENTER)
		self.mainSizer.Add(self.channelSizer, 1, wx.CENTER|wx.EXPAND|wx.TOP|wx.BOTTOM, 10)

		self.SetSizer(self.mainSizer)
 

 # ------------------ Class for Main Frame ----------
	
class MainFrame ( wx.Frame ):
	def __init__( self, parent, items ):
		"""Constructor"""
		wx.Frame.__init__(self, parent=None, title="SpiderScope")
		self.fSizer = wx.BoxSizer(wx.VERTICAL)
		self.channelSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.leftSizer = wx.BoxSizer(wx.VERTICAL)
		self.rightSizer = wx.BoxSizer(wx.VERTICAL)
		self.analogInSizer = wx.BoxSizer(wx.VERTICAL)
		self.analogOutSizer = wx.BoxSizer(wx.VERTICAL)
		self.digitalSizer = wx.BoxSizer(wx.VERTICAL)
		self.leftSizer.Add(self.analogInSizer, 1, wx.EXPAND)
		self.rightSizer.Add(self.analogOutSizer, 0, wx.EXPAND)
		self.rightSizer.Add(self.digitalSizer, 1, wx.EXPAND)
		self.channelSizer.Add(self.leftSizer, 1, wx.EXPAND)
		self.channelSizer.Add(self.rightSizer, 1, wx.EXPAND)

		#loc = wx.IconLocation(r'D:\Python27\python.exe', 0)
		ico = wx.Icon('OFSI-Logo.ico', wx.BITMAP_TYPE_ICO )
		self.SetIcon( ico )


		panel = TopPanel(self)
		self.fSizer.Add(panel, 0, wx.ALL|wx.EXPAND)
		self.fSizer.Add(self.channelSizer, 1, wx.ALL|wx.EXPAND)
		self.SetSizer(self.fSizer)
		self.statusBar = self.CreateStatusBar( 1, wx.ST_SIZEGRIP, wx.ID_ANY )

		self.menuBar = self.createMenubar(items)
		self.SetMenuBar( self.menuBar )
		self.Fit()
		self.Centre(wx.BOTH)
		self.Bind( wx.EVT_CLOSE, self.OnClose )
	def createMenubar(self, items):
		print "Creating Menubar:"
		print items
		menuBar = wx.MenuBar( 0 )
		fileMenu = wx.Menu()
		self.toolsMenu = wx.Menu()
		helpMenu = wx.Menu()

		menuBar.Append(fileMenu, "File")
		menuBar.Append(helpMenu, "Help")

		# create menu items
		rescan = wx.MenuItem( fileMenu, wx.ID_ANY, "Rescan", "Rescans for any attached devices", wx.ITEM_NORMAL )
		sync = wx.MenuItem( fileMenu, wx.ID_ANY, "Sync", "Resyncs channel information between PC and device", wx.ITEM_NORMAL )
		exit = wx.MenuItem( fileMenu, wx.ID_ANY, "Exit", "Closes the application", wx.ITEM_NORMAL )
		about = wx.MenuItem( helpMenu, wx.ID_ANY, "About", "About Box", wx.ITEM_NORMAL ) 

		# append menu items
		#fileMenu.AppendItem(rescan)
		fileMenu.AppendItem(rescan)
		fileMenu.AppendItem(sync)
		fileMenu.AppendItem(exit)
		helpMenu.AppendItem(about)
		# bind items
		self.Bind( wx.EVT_MENU, self.OnRescan, id=rescan.GetId() )
		self.Bind( wx.EVT_MENU, self.OnSync, id=sync.GetId() )
		self.Bind( wx.EVT_MENU, self.OnExit, id=exit.GetId() )
		self.Bind( wx.EVT_MENU, self.OnAbout, id=about.GetId() )
		return menuBar

	def OnSync(self,event):
		pass
	def OnRescan(self, event):
		pass
	def OnExit(self, event):
		self.Close()
	def OnAbout(self, event):
		info = wx.AboutDialogInfo()
		info.SetCopyright("(C) 2012 Optical Fiber Systems inc.")
		info.SetName("SpiderScope Data Aquisition Software")
		info.SetDescription(" software to gather data, perform automated tests, and other functions using the DataSpider modules" )
		info.SetVersion(str(logger.VERSION))
		info.SetWebSite("http://pcdataspider.com")
		wx.AboutBox(info)
	def OnClose(self, event):
		pass


# -------------- RunFor dialog box class --------------------

class RunForDialog ( wx.Dialog ):
	
	def __init__( self, parent, Hrs, Min, Sec ):
		self.cancelled = True
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = "Set Timer", pos = wx.DefaultPosition,  style = wx.DEFAULT_DIALOG_STYLE )
		
		mainSizer = wx.BoxSizer( wx.VERTICAL )
		mainSizer.AddSpacer( ( 0, 10), 0, 0, 0 )
		timerSizer = wx.BoxSizer( wx.HORIZONTAL )
		timerSizer.AddSpacer( ( 0, 0), 1, wx.EXPAND, 0 )
		
		# create spin controls
		self.hours = wx.SpinCtrl( self, wx.ID_ANY, str(Hrs), wx.DefaultPosition, wx.Size( 50,-1 ), wx.SP_ARROW_KEYS, 0, 999, 0 )
		self.minutes = wx.SpinCtrl( self, wx.ID_ANY, str(Min), wx.DefaultPosition, wx.Size( 45,-1 ), wx.SP_ARROW_KEYS, 0, 59, 0 )
		self.seconds = wx.SpinCtrl( self, wx.ID_ANY, str(Sec), wx.DefaultPosition, wx.Size( 45,-1 ), wx.SP_ARROW_KEYS, 0, 59, 0 )
		
		# create labels
		self.hoursTxt = wx.StaticText( self, wx.ID_ANY, "hours", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.minutesTxt = wx.StaticText( self, wx.ID_ANY, "minutes", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.secondsTxt = wx.StaticText( self, wx.ID_ANY, "seconds", wx.DefaultPosition, wx.DefaultSize, 0 )

		# create buttons
		self.ok = wx.Button( self, wx.ID_ANY, "OK", wx.DefaultPosition, wx.DefaultSize, 0 )	
		self.cancel = wx.Button( self, wx.ID_ANY, "Cancel", wx.DefaultPosition, wx.DefaultSize, 0 )

		# add everything to the sizers
		timerSizer.Add( self.hours, 0, wx.LEFT, 0 )
		timerSizer.Add( self.hoursTxt, 0, wx.ALL, 0 )
		timerSizer.Add( self.minutes, 0, wx.LEFT, 5 )
		timerSizer.Add( self.minutesTxt, 0, wx.ALL, 0 )
		timerSizer.Add( self.seconds, 0, wx.LEFT, 5 )
		timerSizer.Add( self.secondsTxt, 0, wx.ALL, 0 )

		# arrange button sizer
		buttonSizer = wx.BoxSizer( wx.HORIZONTAL )
		buttonSizer.AddSpacer( ( 0, 0), 1, wx.EXPAND, 0 )
		buttonSizer.Add( self.cancel, 0, wx.ALL, 0 )
		buttonSizer.Add( self.ok, 0, wx.ALL, 0 )
		
		mainSizer.Add( timerSizer, 1, wx.EXPAND|wx.ALL, 5 )
		mainSizer.Add( buttonSizer, 0, wx.EXPAND|wx.ALL, 0 )
		
		self.SetSizer( mainSizer )
		self.Fit()
		
		self.Centre( wx.BOTH )
		self.Bind(wx.EVT_CLOSE,self.OnClose)
		self.cancel.Bind( wx.EVT_BUTTON, self.On_Cancel )
		self.ok.Bind( wx.EVT_BUTTON, self.On_OK )

	def OnClose( self, event ):
		self.Destroy()
	def On_Cancel( self, event ):
		self.cancelled = True
		self.Close()
	def On_OK( self, event ):
		self.cancelled = False
		self.Close()
		
	
