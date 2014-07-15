import math
import time
import wx
import threading # used for locks
#import wx.lib.buttons as buttons

import logger



# --- Class that defines a channel. 
# class Channel Represents a single input/output channel on the DataSpider module
class Channel():
	name = None		#name of this channel. not neccesarily a number. could be anything
	idx = None		#index of this channel. number used to identify this channel to the controlling prop. 
	started = False
	value = 10000		###
	propCom = None

	widgets = None
	filename = None		# name of the output file
	outFile = None		# file descriptor to write output to. 

	ID = 0		# fixme (used to make a new ID for repeating timers) better way than counter? uuid? TODO
	hooks = dict()


	
	# contructor Channel(PropCom propCom, Int idx, wxWidget widgets, String name, Int startval)
	# return Channel a new Channel object with the specified parameters.
	# propCom = A communication object to use
	# idx = Index for this channel. used for certain control packets and identification
	# widgets = a list of widgets associated with this channel
	# name = A human-readable name for this channel, like "Analog Input 0"
	# startval = Returned object is initialized with this value
	def __init__ (self, propCom, idx, widgets=None, name="?", startval=0):
		"""constructor"""
		self.name = name
		self.idx = idx
		self.widgets = widgets
		self.value = startval
		self.propCom = propCom
		self.started = False
		self.hooks = set()
		self.outfile = None
		self.filename = None

		self.periods = 0
		self.lastTStamp = 0
		self.lastRollover = 0
		self.startTime = 0
		self.startTStamp = None
		self.relTimeStart = None
		
	# destructor Channel() clean up open file handles
	def __del__(self):
		"""destructor to clean up open file handles"""
		if self.outFile is not None:
			self.outFile.close()
			logger.log("Channel destroyed", self.idx, logger.INFO)	
	# Channel.setFile(String fname) return Bool true if successful, false otherwise
	# sets the specified file for recording data.
	# fname = The file to write any data into
	def setFile(self, fname):	# opens a file used to write values into. 
		"""sets this channels output file and overwrites its contents"""
		self.filename = fname
		logger.log("New file for channel " + str(self.idx), self.filename, logger.INFO)
		try:
			self.writeHeader()
		except IOError:
			logger.log("IO Error opening file", self.filename, logger.ERROR)
			logger.message("Can't open file " + self.filename + "\n\nis the file already open?", logger.ERROR)
			self.filename = None
			return False
		else:
			self.openFile() # open file for data. 
			return True
	
	# function Channel.openFile() Open the recording file for writing. The filename is set by Channel.setFile.  The file is opened in "append" mode.
	def openFile(self):
		"""opens this channels output file for writing"""
		if self.filename is not None:
			try:
				self.outfile = open(self.filename, "a")
				logger.log("file opened", self.filename, logger.INFO)
				self.clearTime()
			except ioerror:
				logger.log("io error opening file", self.filename, logger.error)
				logger.message("can't open file " + self.filename + "\n\nis the file already open?", logger.error)
		else:
			logger.log("no file selected. cant open", self.filename, logger.INFO)


	# function Channel.closeFile() close the recording file.
	def closeFile(self):
		"""closes this channels output file"""
		if self.outfile is not None:
			self.outfile.close() 
			logger.log("file closed", self.filename, logger.INFO)
			self.outfile = None
		else:
			logger.log("file already closed", self.filename, logger.INFO)

	# function Channel.writeHeader() opens the recording file and writes header information. Overwrites the file.
	def writeHeader(self):
		"""writes header information into csv file"""
		if self.filename is not None:
			self.outfile = open(self.filename, "w")
			date = '"' + time.asctime() + '"'
			self.outfile.write("channel " + str(self.idx) + "," + date + ',' + 'optical fiber systems\n')
			self.outfile.write("Device clock, time (seconds), value\n" )
			self.closeFile()
			logger.log("header written", self.filename, logger.INFO)

	#function getFilename() return String the current filename of the recording file.
	def getFilename(self):
		"""returns the current filename for log data"""
		if self.filename is None:
			return ""
		else:
			return self.filename


	#function Channel.register(Object obj) return Object the object passed in.
	# Registers the given object to be notified of any events. The object must have methods for any events it wishes to be notified about.
	def register(self,obj):
		self.hooks.add(obj)
		return obj
	#function Channel.deregister(Object obj) Removes the object from being notified of future events on this channel. If the given object is not already registered, a KeyError is raised.
	def deregister(self,obj):
		try:
			self.hooks.remove(obj)
		except KeyError as E:
			logger.log("No function registered in channel " + str(self.idx),  str(obj), logger.WARNING)
			raise

	#function Channel.start() Start this channel. Can have different meaning for different channels.
	def start(self):
		"""sets this channel to started state"""
		self.started = True
		self.openFile()
		self.widgets.startBtn.SetValue(True)
		for obj in self.hooks.copy():
			try:
				obj.onStart(self, self.propCom)
			except Exception as e:
				pass

	#function Channel.stop() Stop this channel. Can have different meaning for different channels.
	def stop(self):
		"""sets this channel to stopped state"""
		self.started = False
		self.closeFile()
		self.widgets.startBtn.SetValue(False)
		for obj in self.hooks.copy():
			try:
				obj.onStop(self, self.propCom)
			except Exception as e:
				logger.log("error with onStop:", e , logger.WARNING)
				pass

	#function Channel.setValue( Anything newval ) Set the value of this channel to *newval*
	def setValue(self, newval):
		"""Change the value of this channel"""
		for obj in self.hooks.copy():
			try:
				obj.onSet(self, self.propCom, newval)
			except Exception as e:
				logger.log("error with onSet:", e , logger.WARNING)
				pass
		self.value = newval

	#function Channel.refresh()
	def refresh(self):
		pass

	#function Channel.clearTime() Resets the time used by Channel.relativeTime
	def clearTime(self):
		"""resets the relativeTime call"""
		self.relTimeStart = None

	#function Channel.relativeTime(Float seconds) return Float time in seconds from the first call to relativeTime to *seconds*, in seconds
	def relativeTime(self, seconds):
		"""returns the relative time since the first call. First call wil return 0. can be reset with clearTime"""
		if self.relTimeStart is None:
			self.relTimeStart = seconds
		return seconds - self.relTimeStart

#	def realTime(self,tStamp):
#		"""return the actual time since epoch when tStamp occured"""
#		now = time.time()
#
#		if self.lastTStamp is None:
#			self.periods = 0
#			self.lastTStamp = 0
#			self.lastRollover = now
#			self.startTime = now
#			self.startTStamp = tStamp
#			
#		# adjust tStamp for calculations
#		tStamp = tStamp - self.startTStamp
#		if tStamp < 0:
#			tStamp += (1<<32) - 1
#
#		if tStamp < self.lastTStamp:
#			self.periods += 1
#			self.lastRollover = now
#		self.lastTStamp = tStamp
#		abstime = self.startTime + self.periods*self.H + float(tStamp)/self.clockFreq
#		return abstime


#function scale_bitmap(wxImage bitmap, Int width, Int height) return a new image with the specified with and height
def scale_bitmap(bitmap, width, height):
    image = wx.ImageFromBitmap(bitmap)
    image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
    result = wx.BitmapFromImage(image)
    return result

#class Channel.Digitals A single class representing all availiable digital channels on the DataSpider module
class Digitals(Channel):
	inVals = 0
	pinDirs = 0
	nPins = 0
	oldValue = 0
	oldInVals = 0

	



	#constructor Digitals(PropCom propCom, Int idx, Int nPins, [wxWidget] widgets, String name, Int startval, Int pinDir)
	# nPins = the number of pins used for digital input/output
	# idx = A single channel index for all digital IO channels
	# startval = The state of all digital outputs as a bitmask. initialized to 0.
	# pinDir = the pin directions for all nPins pins. changing this is NYI.
	def __init__(self, propCom, idx, nPins, widgets=None, name="?", startval=0, pinDir=0):
		Channel.__init__(self, propCom, idx, widgets, name, startval)
		self.onBitmapO = scale_bitmap(wx.Bitmap("green-led-on-md.png"), 30, 30)
		self.offBitmapO = scale_bitmap(wx.Bitmap("green-led-off-md.png"), 30, 30)
		self.onBitmapI = scale_bitmap(wx.Bitmap("blue-led-on-md.png"), 30, 30)
		self.offBitmapI = scale_bitmap(wx.Bitmap("blue-led-off-md.png"), 30, 30)
		self.pinDir=pinDir
		self.nPins = nPins
		self.inVals = 0 	
		self.lock = threading.Lock()
		def idxTest(propCom,  cIdx, *args):
			return cIdx == self.idx
		def dirHook(propCom,  dirs):
			self.pinDirs = dirs
			self.setDir(dirs)
			self.resetWidgets()
		def digHook(propCom,  dVal, tStamp):
			rFalseTime = propCom.realTime(tStamp)
			with self.lock:
				for obj in self.hooks.copy():
						try:
							if obj.digIdx is not None:
								idxmask =  (1<<obj.digIdx) 
							elif obj.digMask:
								idxmask = obj.digMask
							else:
								idxmask = 0

							if (self.inVals ^ dVal) & idxmask: # test if selected idx changed
								if dVal &  idxmask :
									obj.onHigh(self, propCom, dVal, rTime)
								else:
									obj.onLow(self, propCom, dVal, rTime)
							obj.onChange(self, propCom, dVal, rTime)
						except Exception as e:
							logger.log("Error with digHook (channels.py - Digitals) obj=" + str(obj), e, logger.WARNING)

				self.oldValue = self.value
				self.oldInVals = self.inVals
				self.inVals = dVal
				self.recordState()
				self.resetWidgets()
			

		def infoHook(propCom,  cIdx, pVal, dirs):
		#	bitmask = 1 << 31
		#	pVal = (pVal | bitmask) ^ bitmask
			logger.write( pVal )
			self.setValue(int(pVal))
			if self.pinDirs != dirs:
				self.pinDirs = dirs
				self.setDir(dirs)
				self.resetWidgets()

	#	propCom.register("set", setHook, test=idxTest)
	#	propCom.register("dir", dirHook)
		propCom.register("dig", digHook)
		propCom.register("info", infoHook, test=idxTest)
		

	# function Digitals.start() do nothing.
	def start(self):
		pass
	# function Digitals.stop() do nothing.
	def stop(self):
		pass
	# function Digitals.setValue( Int newval, Int pinmask ) 
	# set the state of all digital outputs as a bitmask. pinmask is used to set only a subset of digital outputs. 1=HIGH 0=LOW
	# newval = The new state of digital outputs, as a bitmask
	# pinmask = A bitmask of only the digital outputs to be changed. use None to affect all pins. 1=change, 0=dont change
	def setValue(self, newval, pinmask=None):
		with self.lock:
			if pinmask is not None: 
				newval = ((self.value | pinmask) ^ pinmask) | (newval & pinmask)
			if newval > 255:
				logger.log("digital value too high!!",newval,logger.ERROR)
				newval = 0
			self.oldValue = self.value
			self.oldInVals = self.inVals
			Channel.setValue(self, int(newval))
			self.recordState()
			#bitmask = 1<<31
			#bitmask = bitmask | self.value
			self.propCom.send("set",[self.idx, self.value])
			self.resetWidgets()
		
	# function Digitals.recordState() saves the current state of all digital channels to the recording file set by Digitals.setFile
	def recordState(self):
		''' saves this channels state to a file '''
		oldInVals = self.oldInVals
		oldValue = self.oldValue
		value = self.value
		inVals = self.inVals
		if self.outfile is not None:
			now = self.relativeTime( time.time() )
			#record the old values
			strfmt = str(now)
			mask = 1
			for l in self.widgets.lights:
				if mask & oldValue or mask & oldInVals:
					strfmt += ",1"
				else:
					strfmt += ",0"
				mask = mask << 1
			strfmt += "\n"
			self.outfile.write( strfmt )
			#record the new values
			strfmt = str(now)
			mask = 1
			for l in self.widgets.lights:
				if mask & value or mask & inVals:
					strfmt += ",1"
				else:
					strfmt += ",0"
				mask = mask << 1
			strfmt += "\n"
			self.outfile.write( strfmt )

	# function setDir(Int newval) change the in directions for digital pins. Changing digital channel direction is not supprted. 
	def setDir(self, newval):
		''' change the pin directions for this channel '''
		self.pinDirs = int(newval)
		#mask = 1<<31
		#mask = mask | self.pinDirs
		self.propCom.send("dir", self.pinDirs)
		self.resetWidgetDirs()

	# function Digitals.resetWidgetDirs() Reset the this channels widgets to show the current channel directions
	def resetWidgetDirs(self):
		mask = 1
		for l in self.widgets.lights:
			if mask & self.pinDirs:
				l.SetBitmapLabel(self.offBitmapO)
				l.SetBitmapSelected(self.onBitmapO)
			else:
				l.SetBitmapLabel(self.offBitmapI)
				l.SetBitmapSelected(self.onBitmapI)
			mask = mask << 1
		self.resetWidgets()
	#function Digitals.resetWidgets() reset this channel's widgets to refflect the state of the Digitals object.
	def resetWidgets(self):
		''' resets widgets based on this channel's value '''

		val = self.pinDirs
		mask = 1
		for s in self.widgets.switches:
			if mask & val:
				s.SetValue(True)
			else:
				s.SetValue(False)
			mask = mask << 1
		mask = 1
		for l in self.widgets.lights:
			if mask & self.pinDirs:
				if mask & self.value:
					if not l.GetValue():
						l.SetValue(True)
				else:
					if l.GetValue():
						l.SetValue(False)
			else:
				if mask & self.inVals:
					if not l.GetValue():
						l.SetValue(True)
						pass
				else:
					if l.GetValue():
						l.SetValue(False)
						pass
			mask = mask << 1

	#function Digitals.pinStates(Int pinDirs, Int inVals, Int outVals) return Int bitmask of all the pin states for both inputs and outputs. 1 = HIGH, 0 = LOW
	# pinDirs = bitmask of the current direction of all the pins. 0 = Input, 1 = Output
	# inVals = the state of all input pins as a bitmask
	# outVals = the state of all output pins as a bitmask
	def pinStates(self, pinDirs, inVals, outVals ):
		""" returns a pinmask of all the pin states """
		return (outVals & pinDirs) | (inVals & (~pinDirs))

	#function Digitals.writeHeader()
	def writeHeader(self):
		"""writes header information into csv file"""
		if self.filename is not None:
			self.outfile = open(self.filename, "w")
			date = '"' + time.asctime() + '"'
			self.outfile.write("Digital Channel ," + date + ',' + 'optical fiber systems\n')
			self.outfile.write("time (seconds), DO0, DO1, DO2, DO3, DI0, DI1, DI2, DI3\n" )
			self.closeFile()
			logger.log("header written", self.filename, logger.INFO)



# class Channel.AnalogOut A class for Analog Output channels
class AnalogOut(Channel):
	# constructor AnalogOut(PropCom propCom, Int idx, [Widgets] widgets, String name, Int startval)
	# startval = The output power of the analog output channel from 0-1000
	def __init__(self, propCom, idx, widgets=None, name="?", startval=0000):
		Channel.__init__(self, propCom, idx, widgets, name, startval)
		def idxTest(propCon,  cIdx, *args):
			return cIdx == self.idx

		def infoHook(propCom,  cIdx, pVal, period):
			self.setValue( int(pVal) )
			if bool(pVal) != self.started:
				if bool(pVal):
					self.start()
				else:
					self.stop()

		propCom.register("info", infoHook, test=idxTest)


	# function AnalogOut.start() turns the channel on, and outputs the desired power.
	def start(self):
		Channel.start(self)
		self.propCom.send("set", [self.idx, self.value])
	# function AnalogOut.stop() turn the channel off, cutting all output power.
	def stop(self):
		Channel.stop(self)
		self.propCom.send("set", [self.idx, 0])
	# function AnalogOut.setValue(Int newVal) Set the output power of this channel. If this channel is not on, it will **not** emit power.
	# newVal = Desired output level from 0-1000
	def setValue(self, newval):
		Channel.setValue(self, int(newval))
		if self.started:
			self.propCom.send("set", [self.idx, self.value])
		self.widgets.channelValue.SetValue( str(self.value) )

		if self.outfile is not None:
			strfmt = "{0},{1}\n".format( self.relativeTime( time.time() ), self.value)
			try:
				self.outfile.write( strfmt )
			except ValueError:
				logger.log("Write to file failed", self.filename, logger.WARNING)


	#function AnalogOut.writeHeader()
	def writeHeader(self):
		"""writes header information into csv file"""
		if self.filename is not None:
			self.outfile = open(self.filename, "w")
			date = '"' + time.asctime() + '"'
			self.outfile.write("Analog Out " + str(self.idx - 4) + "," + date + ',' + 'optical fiber systems\n')
			self.outfile.write("time (seconds), value\n" )
			self.closeFile()
			logger.log("header written", self.filename, logger.INFO)

	
#class Channel.AnalogIn A class for an Analog Input channel 
class AnalogIn(Channel):
	started = False
	values = []		#list queue to store values before flushing to disk.
	clockFreq = 80000000


	periods = 0
	lastTStamp = None


	#constructor AnalogIn(PropCom propCom, Int idx, [Widgets] widgets, String name, Int startval)
	# startval = The desired sampling rate for this channel in Clock-ticks Per Sample. (not samples per second)
	def __init__ (self, propCom, idx, widgets=None,  name="?", startval=10000):
		Channel.__init__(self, propCom, idx, widgets, name=name, startval=startval)
		self.clockFreq = propCom.CLOCKPERSEC
		self.H = (math.pow(2,32) -1 ) / self.clockFreq
		self.lastTStamp = None
		self.periods = 0
		def idxTest(propCom,  cIdx, *args):
			return cIdx == self.idx
		def pointIdxTest(propCom, val, *args):
			cIdx = val >> 12
			return cIdx == self.idx


		
	
		def infoHook(propCom,  cIdx, pVal, startmask):
			if pVal == 0:
				pVal = 1
				logger.log("AI infohook", "Rate is infinite!", logger.ERROR)
			sampPsec = (self.clockFreq / float(pVal))
			self.setValue(sampPsec)			

			onstate = (startmask & 1<<cIdx)
			if bool(onstate) != self.started:
				if onstate:
					self.start()
				else:
					self.stop()

		def pointHook(propCom, pVal, tStamp):
			pVal = pVal & 0xFFF
			rTime = propCom.realTime(tStamp)
			self.add(pVal, tStamp, rTime)
			for obj in self.hooks.copy():
				try:
					if logger.options["debug_points"]:
						obj.onPoint(self, propCom, pVal, tStamp, rTime, "SlowFreq")
					else:
						obj.onPoint(self,propCom, pVal, tStamp, rTime)
				except Exception as e:
					logger.log("Error with pointHook (channels.py)", e, logger.WARNING)

		def streamListener(propCom, values):
			rate = values[0]
			tStamp = values[1]
			lastTStamp = values[-1]
			nPoints = len(values[2:-1]) - 1
			if tStamp > lastTStamp:
				rate = ((propCom.MAX_CLOCK - lastTStamp) + tStamp) /nPoints
			else:
				rate = (lastTStamp - tStamp)/nPoints

			rTime = propCom.realTime(tStamp)
			lastRTime = propCom.realTime(lastTStamp)
			rTimeRate =  (float(rate)/propCom.CLOCKPERSEC)


			points = []
			n = 0
			for v in values[2:-1]:
				curTStamp =  tStamp + rate*n
				if curTStamp > propCom.MAX_CLOCK:
					curTStamp = curTStamp - propCom.MAX_CLOCK
				curRTime = rTime + rTimeRate *n
				if curRTime > lastRTime:
					logger.log("Time is too late! math error in streamListener",  str(curRTime) + ">" + str(lastRTime) + " dif:" + str(curRTime - lastRTime))
				if curTStamp > 1<<32:
					curTStamp -= (1<<32)
				point = (v, curTStamp, curRTime )
				points.append( point )
				self.add(*point)
				for obj in self.hooks.copy():
					try:
						if logger.options["debug_points"]:
							obj.onPoint(self, propCom, *point, debugObj="HighFreq - " + str(rate))
						else:
							obj.onPoint(self, propCom, *point)
					except Exception as e:
						logger.log("Error with streamListener (channels.py)", e, logger.WARNING)
				n+=1

		propCom.register("info", infoHook, test=idxTest)
		propCom.register("point", pointHook, test=pointIdxTest)
		propCom.addListener(self.idx,streamListener)

	def setFile(self, fname):
		self.flush()
		return Channel.setFile(self, fname)
		
	def closeFile(self):
		self.flush()
		Channel.closeFile(self)

	def writeHeader(self):
		"""writes header information into csv file"""
		if self.filename is not None:
			self.outfile = open(self.filename, "w")
			date = '"' + time.asctime() + '"'
			self.outfile.write("Analog Input " + str(self.idx) + "," + date + ',' + 'optical fiber systems\n')
			self.outfile.write("time (seconds), value\n" )
			self.closeFile()
			logger.log("header written", self.filename, logger.INFO)

	# AnalogIn.stop() Stop the channel from aquiring more data. Data still left in the DataSpider's buffers may still be recieved.
	def stop(self):
		Channel.stop(self)
		self.propCom.send("stop",1<<self.idx)
		self.lastTStamp = None

	# AnalogIn.start() Start aquiring data from this channel.
	def start(self):
		Channel.start(self)
		self.testAverage()
		self.propCom.send("start",1<<self.idx)
	#AnalogIn.refresh() Resend desired sampling rate, and query the device for its new rate. (The returned rate should be the same.)
	def refresh(self):
		Channel.refresh(self)
		self.propCom.send("set",[self.idx, self.value])
		self.propCom.send("set",[self.idx])

	# AnalogIn.testAverage() Tests the PropCom's sampling average filter to make sure it is safe at the current sample rate. 
	#If the value is too high use PropCom.nAvg to set the desired average rate to a safer value.
	def testAverage(self):
		if self.started and self.value/self.propCom.nAvg<self.propCom.MIN_ADC_PERIOD and self.propCom.nAvg != 1:
			# notify user of change
			self.propCom.nAvg = int(self.value/self.propCom.MIN_ADC_PERIOD)
			logger.message("Average filter is too high. \n Setting to " + str(self.propCom.nAvg) + " sample average.")
			self.propCom.send("avg",self.propCom.nAvg)


	#AnalogIn.setValue(Int newval) Change the sampling rate of this channel to *newval* in samples per second.
	# newval = the desired sampling rate specified in samples-per-second
	def setValue(self, newval):
		"""sets a new sample rate, specified in samples per second, for this channel"""
		Channel.setValue(self, int( self.clockFreq / float(newval) ))

		self.testAverage()
		
		self.propCom.send("set",[self.idx, self.value])
		self.widgets.channelValue.SetValue(str(newval))

	#AnalogIn.flush() Flush any queued data out to the recording file.
	def flush(self):	
		"""flushes any queued data out to a file"""
		for val in self.values:
			if self.outfile is not None:
				strfmt = "{0:.5f},{1}\n".format( self.relativeTime(val[1]) , val[2])
				#strfmt = str( val[0] ) + ","
				#strfmt = str( self.relativeTime(val[1]) ) + ","
				#strfmt += str( val[2] ) + "\n"
				try:
					self.outfile.write( strfmt )
				except ValueError:
					logger.log("Write to file failed", self.filename, logger.WARNING)
			else:
				pass
		self.values = []
	#function AnalogIn.add(Int Val, Int tStamp, Float rTime) Add a value into this channel's data queue.
	#If there is sufficient data, AnalogIn.flush is called.
	def add(self, Val, tStamp, rTime):
		"""add a value into the data queue"""
		data = (tStamp, rTime, Val)
		if logger.options["log_points"]:
			logger.write(self.name + " + (" + str(data) +")")
		self.values.append(data)
		if len(self.values) > logger.options["buffer_size"]:
			self.flush()
	

