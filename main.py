import sys
import os
import imp
import wx
import GUI3
import Propeller
import threading
import RepeatTimer

import logger

# imports for plugins (for compiling)

import Queue
#import wx.lib.plot
import wx.lib.scrolledpanel as scrolled
#import graph
import pickle


nChannels = 4
nAnalogI = 4
nAnalogO = 2
nDigitals = 8

device = None
frame = None
plugins = [] # list of loaded plugin modules
pluginTree = [] # list of menu's

TOOLPATH = "plugins"
PROGRESS_PRECISION = 25
LOGCONSOLE = True
LOGFILE = True

# container class. hold references to all nessesary widgets in a channel sizer.
class ChannelWidgets():
	name = "name"
	panel = None

class AnalogInWidgets (ChannelWidgets):
	name = "name"
	panel = None
	channelValue = None
	startBtn = None
	channelName = None
	runForBtn = None
	progressBar = None

	progressTimers = []
	runForTimer = None

class AnalogOutWidgets(ChannelWidgets):
	channelValue = None
	startBtn = None
	channelName = None
	runForBtn = None
	progressBar = None

	progressTimers = []
	runForTimer = None

class DigitalWidgets(ChannelWidgets):
	lights = None
	switches = None

		

	
	
# subclass of GUI3
class NewGui(GUI3.MainFrame):
	def __init__(self, parent):
		global device
		GUI3.MainFrame.__init__(self, parent, pluginTree) # superclass contructor
		self.Bind( wx.EVT_CLOSE, self.OnClose )
	def buildSubMenu(self, node, parent):
		"""items is a list of tuples to add or a module"""
		logger.write( "Building Submenu:" )
		logger.write( parent )

		name = node[0]
		items = node[1]
		try:
			menu = wx.Menu()
			for i in items:
				logger.write( "adding" )
				self.buildSubMenu(i, menu)
			parent.AppendSubMenu( menu, name )

		except TypeError as e:
			logger.write( "Type Error:" )
			logger.write( e )
			# not a submenu, add as an item
			item = items
			logger.write( "Plugin:" )
			logger.write( item )
			def handler(event): 
				try:
					item.run_tool(self, device)
				except Exception as e:
					logger.log("Unhandled Exception in " + item.title, e, logger.ERROR)
			newitem = wx.MenuItem( parent, wx.ID_ANY, item.title, item.description, wx.ITEM_NORMAL )
			self.Bind( wx.EVT_MENU, handler, id=newitem.GetId())
			parent.AppendItem(newitem)	

		logger.write( "Submenu Built" )
		return menu
	def buildMenus(self, items, menuBar):
		"""items is a list of tuples"""
		logger.write( "Building Menus" )
		for i in items:
			logger.write( "Building " + i[0] + " Menu" )
			name = i[0]
			menu = wx.Menu()
			menuBar.Append( self.buildSubMenu(i, menu), name )
	def createMenubar(self, items):
		logger.write( "Creating Menubar:" )
		logger.write( items )
		menuBar = wx.MenuBar( 0 )
		fileMenu = wx.Menu()
		self.toolsMenu = wx.Menu()
		helpMenu = wx.Menu()

		menuBar.Append(fileMenu, "File")
		self.buildMenus(items, menuBar)
		menuBar.Append(helpMenu, "Help")

		# create menu items
		rescan = wx.MenuItem( fileMenu, wx.ID_ANY, "Rescan", "Rescans for any attached devices", wx.ITEM_NORMAL )
		reloadtools = wx.MenuItem( fileMenu, wx.ID_ANY, "Reload Plugins", "Rescans plugin directory and loads changes", wx.ITEM_NORMAL )
		exit = wx.MenuItem( fileMenu, wx.ID_ANY, "Exit", "Closes the application", wx.ITEM_NORMAL )
		about = wx.MenuItem( helpMenu, wx.ID_ANY, "About", "About Box", wx.ITEM_NORMAL ) 

		# append menu items
		#fileMenu.AppendItem(rescan)
		fileMenu.AppendItem(reloadtools)
		fileMenu.AppendItem(exit)
		helpMenu.AppendItem(about)
		# bind items
		self.Bind( wx.EVT_MENU, self.OnRescan, id=rescan.GetId() )
		self.Bind( wx.EVT_MENU, self.OnReload, id=reloadtools.GetId() )
		self.Bind( wx.EVT_MENU, self.OnExit, id=exit.GetId() )
		self.Bind( wx.EVT_MENU, self.OnAbout, id=about.GetId() )
		return menuBar
	
		
	def OnReload( self, event):
		importTools(TOOLPATH)
		self.menuBar = self.createMenubar(pluginTree)
		self.SetMenuBar( self.menuBar )
		self.Fit()
	def OnRescan( self, event):
		global device
		device.propCom = device.propCom.restart()
	def OnClose( self, event):
		self.Destroy()
		logger.log("Frame closed", "", logger.INFO)
		for ID,t in device.propCom.locks.iteritems():
			logger.log("killing lock",ID, logger.INFO)
			t.cancel()
		for ID,w in self.widgets.iteritems():
			for t in w.progressTimers:
				t.cancel()
			if w.runForTimer is not None:
				w.runForTimer.cancel()
	# ----- widgets handler functions -----
	def On_Switch(self, event, idx):
		global device
		if device.propCom.isOpen() == False:
			for w in self.widgets[idx].switches:
				w.SetValue(False)
			if logger.ask("No Propeller attached. Rescan ports?", "Error"):
				device.propCom.start()
		else:
			bitmask = 0
			for w in self.widgets[idx].switches[::-1]:
				bitmask = bitmask << 1
				if w.GetValue():
					bitmask = bitmask | 1
			device.digitals.setDir(bitmask)

	def On_Light(self, event, idx):
		global device
		if device.propCom.isOpen() == False:
			for w in self.widgets[idx].lights:
				w.SetValue(False)
			if logger.ask("No Propeller attached. Rescan ports?", "Error"):
				device.propCom.start()
		else:
			bitmask = 0
			for w in self.widgets[idx].lights[::-1]:
				bitmask = bitmask << 1
				if w.GetValue():
					bitmask = bitmask | 1
			device.digitals.setValue(bitmask)


	def On_ValueChange( self, event, idx):
		global device
		try:
			value = float(self.widgets[idx].channelValue.GetValue())
			device.channels[idx].setValue(value)
			value = device.channels[idx].value
		except ValueError:
			self.widgets[idx].channelValue.SetLabel("NaN")

	def On_Record( self, event, idx):
		global device
		if self.widgets[idx].recordBtn.GetValue():
			filetypes = "CSV files (*.csv)|*.csv|Text files (*.txt)|*.txt|All files|*"
			dlg = wx.FileDialog(self, "Choose a file", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT, wildcard=filetypes)
			outFile = None
			if dlg.ShowModal()==wx.ID_OK:
				try:
					filename=dlg.GetFilename()
					dirname=dlg.GetDirectory()
					fullPath = os.path.join(dirname, filename)
					if not device.channels[idx].setFile(fullPath):
						self.widgets[idx].recordBtn.SetValue(False)
						device.channels[idx].closeFile()
					else:
						device.channels[idx].openFile()
				except Exception as e:
					logger.log("Error setting recording file", e, logger.ERROR)
			else:
					device.channels[idx].setFile(None)
					self.widgets[idx].recordBtn.SetValue(False)
					device.channels[idx].closeFile()
		else:
					device.channels[idx].setFile(None)
					device.channels[idx].closeFile()

		
	def On_StartStop( self, event, idx):
		global device
		if device.propCom.isOpen() == False:
			self.widgets[idx].startBtn.SetValue(False) 
			if logger.ask("No Propeller attached. Rescan ports?", "Error" ):
				device.propCom.start()
		if	self.widgets[idx].startBtn.GetValue():
			if self.widgets[idx].runForTimer is not None:
				device.channels[idx].start()
				for t in self.widgets[idx].progressTimers:
					t.start()
				self.widgets[idx].runForTimer.start()
			else:
				device.channels[idx].start()
				self.widgets[idx].progressBar.SetValue(0)
		else:
			device.channels[idx].stop()
			self.widgets[idx].timerText.SetLabel("000:00:00")
			self.widgets[idx].timerText.Enable(False)
			self.widgets[idx].progressBar.SetValue(0)
			for t in self.widgets[idx].progressTimers:
				t.cancel()
			self.widgets[idx].progressTimers = []
			if self.widgets[idx].runForTimer is not None:
				self.widgets[idx].runForTimer.cancel()
				self.widgets[idx].runForTimer = None
	
	def On_RunFor( self, event, idx):
		global device
		cHrs = self.widgets[idx].timerText.GetLabel()[:3]
		cMin = self.widgets[idx].timerText.GetLabel()[4:6]
		cSec = self.widgets[idx].timerText.GetLabel()[7:9]
		runForBox = GUI3.RunForDialog(self,cHrs,cMin,cSec)
		runForBox.ShowModal()
		if runForBox.cancelled:
			return
		else:

			runForSeconds = runForBox.hours.GetValue()*2400 +runForBox.minutes.GetValue()*60 + runForBox.seconds.GetValue()
			timer = []
			timer.append(runForBox.seconds.GetValue())
			timer.append(runForBox.minutes.GetValue())
			timer.append(runForBox.hours.GetValue())
			timeFormat = "{0:03}:{1:02}:{2:02}".format( runForBox.hours.GetValue(),runForBox.minutes.GetValue(), runForBox.seconds.GetValue() )
			self.widgets[idx].timerText.SetLabel(timeFormat)
			self.widgets[idx].timerText.Enable(True)

			self.widgets[idx].progressBar.SetRange(PROGRESS_PRECISION)
			self.widgets[idx].progressBar.SetValue(0)

			def decTimer():
			
				timer[0] -= 1
				if timer[0] < 0:
					timer[1] -=1
					timer[0] = 59
				if timer[1] < 0:
					timer[2] -=1
					timer[1] = 59
					timer[0] = 59
				if timer[2] < 0:
					timer[2] = 0
					timer[1] = 0
					timer[0] = 0

				timeFormat = "{0:03}:{1:02}:{2:02}".format( timer[2],timer[1],timer[0] )
				self.widgets[idx].timerText.SetLabel(timeFormat)

			def incGauge():
				newVal = self.widgets[idx].progressBar.GetValue() + 1
				self.widgets[idx].progressBar.SetValue(newVal)

			self.widgets[idx].progressTimers = []
			self.widgets[idx].progressTimers.append(RepeatTimer.Timer(1, True, decTimer))
			for n in range(PROGRESS_PRECISION-1):
				self.widgets[idx].progressTimers.append(threading.Timer((n+1)*(float(runForSeconds)/PROGRESS_PRECISION),incGauge)) 

			def onStop():
				# TODO is GUI still alive???
				self.widgets[idx].timerText.Enable(False)
				for t in self.widgets[idx].progressTimers:
					t.cancel()
				self.progressTimers = []
				self.widgets[idx].runForTimer = None
				self.widgets[idx].progressBar.SetRange(100)
				self.widgets[idx].progressBar.SetValue(100)
				device.channels[idx].stop()

			self.widgets[idx].runForTimer = threading.Timer(runForSeconds,onStop)


	
	# ----- helper functions	
	def addAnalogIn(self, name, idx):
		""" Adds another channel into the GUI and returns a container with the widgets"""
		newChannel = GUI3.AnalogInPanel(self, name, idx)
		self.analogInSizer.Add( newChannel, 0, wx.TOP|wx.LEFT|wx.RIGHT|wx.EXPAND,5)
		newChannel.Layout()
		self.Layout()
		self.Fit() 
		# wrap necessary widgets into a container class for access
		widgets = AnalogInWidgets()
		widgets.panel = newChannel
		widgets.channelName= newChannel.channelName
		widgets.channelValue= newChannel.sampleRate
		widgets.startBtn= newChannel.startBtn
		widgets.runForBtn= newChannel.runForBtn
		widgets.progressBar= newChannel.progressBar
		widgets.timerText= newChannel.timer
		widgets.recordBtn = newChannel.recordBtn
		# create closures for handler functions
		def this_RateChange(event):
			self.On_ValueChange( event, idx)
		def this_Record(event):
			self.On_Record(event, idx)
		def this_StartStop(event):
			self.On_StartStop(event, idx)
		def this_RunFor(event):
			self.On_RunFor(event, idx)
		# now bind all widgets to handler function)
		widgets.channelValue.Bind( wx.EVT_TEXT_ENTER, this_RateChange )
		widgets.channelValue.Bind( wx.EVT_KILL_FOCUS, this_RateChange )
		widgets.startBtn.Bind( wx.EVT_BUTTON, this_StartStop )
		widgets.recordBtn.Bind( wx.EVT_BUTTON, this_Record )
		widgets.runForBtn.Bind( wx.EVT_BUTTON, this_RunFor )

		# return
		return widgets
	def addAnalogOut(self, name, idx):
		""" Adds another channel into the GUI and returns a container with the widgets"""
		newChannel = GUI3.AnalogOutPanel(self, name, idx)
		self.analogOutSizer.Add( newChannel, 0, wx.TOP|wx.LEFT|wx.RIGHT|wx.EXPAND,5)
		newChannel.Layout()
		self.Layout()
		self.Fit() 
		# wrap necessary widgets into a container class for access
		widgets = AnalogOutWidgets()
		widgets.panel = newChannel
		widgets.channelName= newChannel.channelName
		widgets.channelValue= newChannel.outputPwr
		widgets.startBtn= newChannel.startBtn
		widgets.runForBtn= newChannel.runForBtn
		widgets.progressBar= newChannel.progressBar
		widgets.timerText= newChannel.timer
		widgets.recordBtn = newChannel.recordBtn
		# create closures for handler functions
		def this_PwrChange(event):
			self.On_ValueChange( event, idx)
		def this_Record(event):
			self.On_Record(event, idx)
		def this_StartStop(event):
			self.On_StartStop(event, idx)
		def this_RunFor(event):
			self.On_RunFor(event, idx)
		# now bind all widgets to handler functions
		widgets.channelValue.Bind( wx.EVT_KILL_FOCUS, this_PwrChange )
		widgets.channelValue.Bind( wx.EVT_TEXT_ENTER, this_PwrChange )
		widgets.recordBtn.Bind( wx.EVT_BUTTON, this_Record )
		widgets.startBtn.Bind( wx.EVT_BUTTON, this_StartStop )
		widgets.runForBtn.Bind( wx.EVT_BUTTON, this_RunFor )

		# return
		return widgets
	def addDigital(self, name, idx, n):
		""" Addr another channel into the GUI and returns a container with the widgets"""
		newChannel = GUI3.DigitalPanel(self, name, idx, n)
		self.digitalSizer.Add( newChannel, 0, wx.TOP|wx.LEFT|wx.RIGHT|wx.EXPAND,5)
		newChannel.Layout()
		self.Layout()
		self.Fit() 
		# wrap necessary widgets into a container class for access
		widgets = DigitalWidgets()
		widgets.panel = newChannel
		widgets.channelName= newChannel.channelName
		widgets.recordBtn = newChannel.recordBtn

		widgets.lights = newChannel.lights
		widgets.switches = newChannel.switches
		# create closures for handler functions
		def this_Record(event):
			self.On_Record(event, idx)
		def this_Switch(event):
			self.On_Switch( event, idx)
		def this_Light(event):
			self.On_Light(event, idx)
		widgets.recordBtn.Bind( wx.EVT_BUTTON, this_Record )
		# now bind all widgets to handler functions
		for l in widgets.lights:
			l.Bind( wx.EVT_BUTTON, this_Light )
		for s in widgets.switches:
			s.Bind( wx.EVT_BUTTON, this_Switch )

		# return
		return widgets
	# ----- enables / disables start controls
	def propEnabled(self, enabled=True):
		for i, c in frame.widgets.iteritems():
			c.startBtn.Enable(enabled)
			c.runForBtn.Enable(enabled)

	# ----- creates all the channels -----
	def createChannels(self, device):
		self.widgets = dict() 
		for idx, chan in device.analogIn.iteritems():
			name = chan.name
			self.widgets[idx] = self.addAnalogIn(name, idx) # adds the widgets of this channel into a dict
			chan.widgets = self.widgets[idx]
		for idx, chan in device.analogOut.iteritems():
			name = chan.name
			self.widgets[idx] = self.addAnalogOut(name, idx)
			chan.widgets = self.widgets[idx]

		name = device.digitals.name
		idx = device.digitals.idx
		n = device.digitals.nPins
		self.widgets[idx] = self.addDigital(name, idx, n)
		device.digitals.widgets = self.widgets[idx]
	




	
def testplugin(module):
	"""returns True if module has nessesary parameters"""
	logger.write( module.title )
	return True # dummy

def addTools(searchdir):
	"""searches a directory and returns a list of tuples."""
	items = []
	name = "?"
	files = os.listdir( searchdir)
	sys.path.append( searchdir )
	for f in files:
		name = f
		fullPath = os.path.join(searchdir, f)
		if os.path.isdir( fullPath ):
			items.append( (name, addTools(fullPath)) )
		elif f[-3:] == ".py":
			name = f[:-3]
			mod = imp.load_source(name, fullPath)
			if testplugin(mod):
				logger.write( name + " <-" )
				items.append((name,mod))
				logger.log("Loaded Plugin", mod, logger.INFO)
	return items

def importTools(relPath):
	"""searches a directory and fills pluginTree"""
	global pluginTree
	global pludins

	plugins = [] # list of loaded plugin modules
	pluginTree = [] # list of menu's

	cwd = os.getcwd()
	toolDirPath = os.path.join(cwd, relPath)
	try:
		files = os.listdir( toolDirPath )
	except Exception as e:
		logger.log("Could not load plugin directory.", e, logger.WARNING)
		return
	for f in files:
		fullpath = os.path.join(toolDirPath, f)
		if os.path.isdir( fullpath ):
			pluginTree.append((f, addTools(fullpath))) 
		else:
			logger.log("Bad plugin in base directory", f, logger.WARNING)

# ----- Starts Here -----		
def main():
	global device
	global frame
	# start logger
	if LOGFILE:
		logger.outFile = open( logger.fName, "w" )
	if LOGCONSOLE:
		logger.console = True
	# load all "plugin" modules. 
	try:
		importTools(TOOLPATH)
	except Exception as e:
		logger.log("Could not load tools:", e, logger.WARNING)
	# make GUI
	app = wx.PySimpleApp()
	frame = NewGui(None)


	# setup propeller object
	device = Propeller.Device(nAnalogI, nAnalogO, nDigitals, )

	# define message handlers
	def versionHandler(propCom,  ver):
		#if val is None:
		#	PropCom.send("version",VERNUM)
		#else:
		logger.log("Propeller version", ver, logger.INFO)


	def setHandler(propCom,  cIdx, pVal):
		#if val is None:
		#	logger.log("bad request", "set", logger.ERROR)
		#else:
		try:
			#cIdx = val[0]
			#pVal = val[1]
			if cIdx not in device.channels:
				logger.log("invalid channel index", str(cIdx), logger.WARNING)
			else:
				logger.write( "." )
				#device.channels[cIdx].
				#device.channels[cIdx].setValue(pVal)
				#frame.widgets[cIdx].setChan(device.channels[cIdx])
		except IndexError as e:
			logger.log("not enough values", "set", logger.ERROR)

	def startHandler(propCom,  mask):
		#if val is None:
		#	logger.log("bad request", "start", logger.ERROR)
		#else:
		logger.log("started channels", mask, logger.INFO)
		#mask = val[0]
		for cIdx,chan in device.analogIn.iteritems(): 
			if not ((mask&(1<<chan.idx)>0) == chan.started): # test if this channel is correct
				# not correct. correct the prop. 
				logger.log("Channels dont match", chan.idx, logger.INFO)
				if chan.started:
					chan.start()
				else:
					chan.stop()
				propCom.send("start")

	def nchannelsHandler(propCom, nchans):
		"""Start of dialog between propeller and PC"""
		global frame
		#if val is None:
		#	logger.log("bad request", "nChannel", logger.ERROR)
		#else:
		logger.log("nChannels", nchans, logger.INFO)
		# channels are added. register channels info functions
		#propCom.register("set", setHandler)
		propCom.register("start", startHandler)
		#propCom.register("dir", dirHandler)
		#propCom.register("d", digHandler)
		device.queryChannel()
		# prop state should now be setup. handle incoming data points. 
		#propCom.register("p", pointHandler)
			


	device.propCom.register("nchannels", nchannelsHandler)
	device.propCom.register("version", versionHandler)

	frame.createChannels(device)
	frame.Centre(wx.BOTH)

	device.propCom.start()	# start prop, begins polling open ports

	# setup complete, show frame. 
	frame.Show()
	app.MainLoop()

	# program termination.  
	device.propCom.close()
	if LOGFILE:
		logger.outFile.close()

# start program
main()
