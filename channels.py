import math
import time
import wx
import threading # used for locks
#import wx.lib.buttons as buttons

import logger

POINTLOG = False
MAXBUFFER = 500


# --- Class that defines a channel. 
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
		
	def __del__(self):
		"""destructor to clean up open file handles"""
		if self.outFile is not None:
			self.outFile.close()
			logger.log("Channel destroyed", self.idx, logger.INFO)	
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


	def closeFile(self):
		"""closes this channels output file"""
		if self.outfile is not None:
			self.outfile.close() 
			logger.log("file closed", self.filename, logger.INFO)
			self.outfile = None
		else:
			logger.log("file already closed", self.filename, logger.INFO)

	def writeHeader(self):
		"""writes header information into csv file"""
		if self.filename is not None:
			self.outfile = open(self.filename, "w")
			date = '"' + time.asctime() + '"'
			self.outfile.write("channel " + str(self.idx) + "," + date + ',' + 'optical fiber systems\n')
			self.outfile.write("Device clock, time (seconds), value\n" )
			self.closeFile()
			logger.log("header written", self.filename, logger.INFO)

	def getFilename(self):
		"""returns the current filename for log data"""
		if self.filename is None:
			return ""
		else:
			return self.filename


	def register(self,obj):
		self.hooks.add(obj)
		return obj
	def deregister(self,obj):
		try:
			self.hooks.remove(obj)
		except KeyError as E:
			logger.log("No function registered in channel " + str(self.idx),  str(obj), logger.WARNING)
			raise

	def start(self):
		"""sets this channel to started state"""
		self.started = True
		self.widgets.startBtn.SetValue(True)
		for obj in self.hooks.copy():
			try:
				obj.onStart(self, self.propCom)
			except Exception as e:
				pass

	def stop(self):
		"""sets this channel to stopped state"""
		self.started = False
		self.widgets.startBtn.SetValue(False)
		for obj in self.hooks.copy():
			try:
				obj.onStop(self, self.propCom)
			except Exception as e:
				logger.log("error with onStop:", e , logger.WARNING)
				pass

	def setValue(self, newval):
		"""Change the value of this channel"""
		for obj in self.hooks.copy():
			try:
				obj.onSet(self, self.propCom, newval)
			except Exception as e:
				logger.log("error with onSet:", e , logger.WARNING)
				pass
		self.value = newval

	def clearTime(self):
		"""resets the relativeTime call"""
		self.relTimeStart = None

	def relativeTime(self, seconds):
		"""returns the relative time since the first call. First call wil return 0. can be reset with clearTime"""
		if self.relTimeStart is None:
			self.relTimeStart = seconds
		return seconds - self.relTimeStart

	def realTime(self,tStamp):
		"""return the actual time since epoch when tStamp occured"""
		now = time.time()

		if self.lastTStamp is None:
			self.periods = 0
			self.lastTStamp = 0
			self.lastRollover = now
			self.startTime = now
			self.startTStamp = tStamp
			
		# adjust tStamp for calculations
		tStamp = tStamp - self.startTStamp
		if tStamp < 0:
			tStamp += (1<<32) - 1

		if tStamp < self.lastTStamp:
			self.periods += 1
			self.lastRollover = now
		self.lastTStamp = tStamp
		abstime = self.startTime + self.periods*self.H + float(tStamp)/self.clockFreq
		return abstime


#helper function -------
def scale_bitmap(bitmap, width, height):
    image = wx.ImageFromBitmap(bitmap)
    image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
    result = wx.BitmapFromImage(image)
    return result

class Digitals(Channel):
	inVals = 0
	pinDirs = 0
	nPins = 0
	oldValue = 0
	oldInVals = 0

	



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
			logger.write("digHook hit")
			with self.lock:
				for obj in self.hooks.copy():
						try:
							if obj.digIdx is not None:
								idxmask =  (1<<obj.digIdx) 
							else:
								idxmask = 0
							if (self.inVals ^ dVal) & idxmask: # test if selected idx changed
								if dVal &  idxmask :
									obj.onHigh(self, propCom, dVal)
								else:
									obj.onLow(self, propCom, dVal)
							obj.onChange(self, propCom, dVal)
						except Exception as e:
							logger.log("Error with digHook (channels.py - Digitals) obj=" + str(obj), e, logger.WARNING)

				self.oldValue = self.value
				self.oldInVals = self.inVals
				self.inVals = dVal
				self.recordState()
				self.resetWidgets()
			

		def setHook(propCom,  cIdx, pVal):
			bitmask = 1 << 31
			pVal = (pVal | bitmask) ^ bitmask
			logger.write( pVal )
			self.setValue(int(pVal))

		propCom.register("set", setHook, test=idxTest)
		propCom.register("dir", dirHook)
		propCom.register("d", digHook)
		

	def start(self):
		pass
	def stop(self):
		pass
	def setValue(self, newval, pinmask=None):
		logger.write("setValue hit")
		with self.lock:
			if pinmask is not None: 
				newval = ((self.value | pinmask) ^ pinmask) | (newval & pinmask)
			if newval > 255:
				logger.log("digital value too high!!",newval,logger.ERROR)
				newval = 0
			logger.write( str(self.value) + "=>" + str(newval) )
			logger.write( newval )
			logger.write( self.value )
			self.oldValue = self.value
			self.oldInVals = self.inVals
			Channel.setValue(self, int(newval))
			self.recordState()
			logger.write( self.value )
			bitmask = 1<<31
			bitmask = bitmask | self.value
			self.propCom.send("set",[self.idx, bitmask])
			self.resetWidgets()
		
	def recordState(self):
		''' saves this channels state to a file '''
		oldInVals = self.oldInVals
		oldValue = self.oldValue
		value = self.value
		inVals = self.inVals
		if self.outfile is not None:
			#now = self.realTime()
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

	def setDir(self, newval):
		''' change the pin directions for this channel '''
		self.pinDirs = int(newval)
		mask = 1<<31
		mask = mask | self.pinDirs
		self.propCom.send("dir", mask)
		self.resetWidgetDirs()

	def resetWidgetDirs(self):
		''' resets the pin directions for this channel and update the widgets to match '''
		#mask = 1
		#for w in self.widgets.labels: #TODO fix use of "labels" widgets. 
		#	if mask & self.pinDirs:
		#		w.SetLabel("Output")
		#	else:
		#		w.SetLabel("Input")
		#	mask = mask << 1	
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

	def pinStates(self, pinDirs, inVals, outVals ):
		""" returns a pinmask of all the pin states """
		return (outVals & pinDirs) | (inVals & (~pinDirs))
	def writeHeader(self):
		"""writes header information into csv file"""
		if self.filename is not None:
			self.outfile = open(self.filename, "w")
			date = '"' + time.asctime() + '"'
			self.outfile.write("Digital Channel ," + date + ',' + 'optical fiber systems\n')
			self.outfile.write("time (seconds), DO0, DO1, DO2, DO3, DI0, DI1, DI2, DI3\n" )
			self.closeFile()
			logger.log("header written", self.filename, logger.INFO)



class AnalogOut(Channel):
	def __init__(self, propCom, idx, widgets=None, name="?", startval=0000):
		Channel.__init__(self, propCom, idx, widgets, name, startval)
		def idxTest(propCon,  cIdx, *args):
			return cIdx == self.idx

		def setHook(propCom,  cIdx, pVal):
			self.setValue( int(pVal) )
			#self.value = int(pVal)
			#self.widgets.channelValue.SetValue(str(self.value))

		propCom.register("set", setHook, test=idxTest)


	def start(self):
		Channel.start(self)
		self.propCom.send("set", [self.idx, self.value])
	def stop(self):
		Channel.stop(self)
		self.propCom.send("set", [self.idx, 0])
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

	def writeHeader(self):
		"""writes header information into csv file"""
		if self.filename is not None:
			self.outfile = open(self.filename, "w")
			date = '"' + time.asctime() + '"'
			self.outfile.write("Analog Out " + str(self.idx - 4) + "," + date + ',' + 'optical fiber systems\n')
			self.outfile.write("time (seconds), value\n" )
			self.closeFile()
			logger.log("header written", self.filename, logger.INFO)

	
class AnalogIn(Channel):
	started = False
	values = []		#list queue to store values before flushing to disk.
	clockFreq = 80000000


	periods = 0
	lastTStamp = None


	def __init__ (self, propCom, idx, widgets=None,  name="?", startval=10000):
		Channel.__init__(self, propCom, idx, widgets, name=name, startval=startval)
		self.clockFreq = propCom.CLOCKPERSEC
		self.H = (math.pow(2,32) -1 ) / self.clockFreq
		self.lastTStamp = None
		self.periods = 0
		def idxTest(propCom,  cIdx, *args):
			return cIdx == self.idx

		
	
		def setHook(propCom,  cIdx, pVal):
			self.value = int(pVal)
			sampPsec = self.clockFreq / float(pVal)
			self.widgets.channelValue.ChangeValue(str(sampPsec))
			for obj in self.hooks.copy():
				try:
					obj.onSet(self, propCom, pVal, sampPsec)
				except Exception as e:
					pass
			
		def pointHook(propCom,  cIdx, pVal, tStamp):
			try:
				rTime = self.realTime(tStamp)
				self.add(pVal,tStamp,rTime)
				for obj in self.hooks.copy():
					try:
						obj.onPoint(self, propCom, pVal, tStamp, rTime)
					except Exception as e:
						logger.log("Error with pointHook (channels.py)", e, logger.WARNING)
			except ValueError as e:
				logger.log("Incorrect values to 'p'", e, logger.WARNING)
			except TypeError as e:
				logger.log("Incorrect types to 'p'", e, logger.WARNING)

		propCom.register("set", setHook, test=idxTest)
		propCom.register("p", pointHook, test=idxTest)

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

	def stop(self):
		Channel.stop(self)
		self.propCom.send("stop",1<<self.idx)
		self.lastTStamp = None

	def start(self):
		Channel.start(self)
		self.propCom.send("start",1<<self.idx)

	def setValue(self, newval):
		Channel.setValue(self, int( self.clockFreq / float(newval) ))
		
		self.propCom.send("set",[self.idx, self.value])
		self.widgets.channelValue.SetValue(str(newval))

	def flush(self):	
		"""flushes any queued data out to a file"""
		#print "flushing " + str( len(self.values) ) + " values at " + str( time.time() )
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
	def add(self, Val, tStamp, rTime):
		"""add a value into the data queue"""
		data = (tStamp, rTime, Val)
		if POINTLOG:
			print self.name + " + (" + str(data) +")"
		self.values.append(data)
		if len(self.values) > MAXBUFFER:
			self.flush()
	

