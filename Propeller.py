import serial
import serial.tools.list_ports
import time
import re
import threading
import RepeatTimer
import sys
import math
import inspect


import channels
import logger


DEFAULTBAUD = 115200	# BAUD rate to communicate at
#DEFAULTBAUD = 57600	# BAUD rate to communicate at
DEFAULTTIMEOUT = .5	# Timeout for propellor to respond
DEFAULTREADSLEEP = 0.1 	# Time that the read loop sleeps for. 
DEFAULTFLUSH = 1 	# Interval to flush channel data 
DEFAULTOUTFILE = "test.txt"
MAX_EID = 200
MSG_HEAD = 2
VERNUM = 10		# version 1.0
EOP = "|"
ESC = "`"

IGNORECHKSUM = False #ignores bad checksums
PARSELOG = False # turns on debugging info in the parse function.
MSGLOG = False # turns on logging every message in the log.
CTRLLOG = True # turns on logging of control messages and their parameters in log. does not include point messages.
STREAMLOG = False # turns on logging every stream packet in the log. 
#POINTLOG = False #<- look in channels.py. turns on logging every point through the AnalogI channel interface. 

p_key = re.compile("""<(([^<>@:]+?))(:((([^<>'",#$:]*)|(#.{4})|(\$.{2})|(['"].*?['"])),)*(([^<>'",#$:]*)|(#.{4})|(\$.{2})|(['"].*?['"]))?)?>""", re.DOTALL)  # Matches Any Key!
p_wholename = re.compile("<[^@:]*?[:]", re.DOTALL) # matches the entire name including <..|...:  (must have value field)
p_name = re.compile("<[^@:]*?[:>]", re.DOTALL) # matches only the name of the key including "< ... :" (no echo) 
p_wholeval = re.compile(""":(((['"][^'"]*['"])|(#.{4})|(\$.{2})|([^<>'",#$:]*)),)*((#.{4})|(\$.{2})|([^<>"',#$:]*)|(['"][^'"]*['"]))?>""", re.DOTALL) # matches only the value of the key including ": ... >"
p_val = re.compile("""(((['"][^'"]*['"])|(#.{4})|(\$.{2})|([^<>'",#$:]*)),)|(((['"][^'"]*['"])|(#.{4})|(\$.{2})|([^<>'",#$:]*))>)""", re.DOTALL) # matches only a single value of the value fiel

#keyTable = {0:"talk",1:"over",2:"bad",3:"version",4:"start",5:"stop",6:"set",7:"dir",8:"query",9:"info",10:"dig",11:"wav"} 
keyTable = ["talk","over","bad","version","start","stop","set","dir","query","info","dig","wav","point","sync","avg"]


# -- Class that holds one integer point.
class Data():
	time = 0	# absolute time this data was taken
	systime = 0	# system time this data point was recieved
	clk = 0		# prop clock time this data point was taken
	value = 0	# value of this data point
	def __init__(self,rtime, clk, value):
		self.systime = time.time() # ticks since epoch
		self.time = rtime
		self.clk = clk
		self.value = value
	
	def __str__(self):
		return str(self.systime) + "," + str(self.time) + "," + str(self.clk) + "," + str(self.value) + "\n"

class Device():
	propCom = None
	analogIn = dict()
	analogOut = dict()
	digitals = None
	def __init__(self, nAnalogI, nAnalogO, nDigitals):
		self.propCom = PropCom()
		self.analogIn = dict()
		self.analogOut = dict()
		self.digitals = None
		self.channels = dict()
		self.digitalIdx = nAnalogI + nAnalogO

		for idx in range(nAnalogI):
			name = "Analog Input " + str(idx)
			cIdx = idx
			self.analogIn[cIdx] = channels.AnalogIn( self.propCom, cIdx, name=name ) 
			self.channels[cIdx] = self.analogIn[cIdx]
		for idx in range(nAnalogO):
			name = "Analog Output " + str(idx)
			cIdx = idx + nAnalogI
			self.analogOut[cIdx] = channels.AnalogOut( self.propCom, cIdx, name=name) 
			self.channels[cIdx] = self.analogOut[cIdx]

		name = "Digital I/O"
		cIdx = nAnalogI + nAnalogO
		self.digitals = channels.Digitals( self.propCom, cIdx, nDigitals, name=name)  
		self.channels[cIdx] = self.digitals


	def setNAvg(self, nAvg):
		if nAvg < 1:
			nAvg = 1
		self.propCom.nAvg = int(nAvg)

		for x in self.analogIn:
			idx = self.channels[x].idx
			if self.channels[x].started and self.channels[x].value/self.propCom.nAvg<self.propCom.MIN_ADC_PERIOD and self.propCom.nAvg != 1:
				self.setNAvg(self.channels[x].value/self.propCom.MIN_ADC_PERIOD)
				# notify user of change
				logger.message("Average filter is too high. \n Setting to " + str(self.propCom.nAvg) + " sample average.")

		self.propCom.send("avg", self.propCom.nAvg)
		
	#query prop about the state of a certain channel
	def queryChannel(self, chan=None):
		if chan is None:
			for x in self.analogIn:
				idx = self.channels[x].idx
				self.propCom.send("query", idx)
			for x in self.analogOut:
				idx = self.channels[x].idx
				self.propCom.send("query", idx)
			idx = self.digitals.idx
			self.propCom.send("query", idx)
		else:
			if chan in self.channels:
				idx = self.channels[chan].idx
				self.propCom.send("query", idx)
			else:
				logger.log("Bad Channel Querry", chan, logger.WARNING)





# --- The communication object. Represents methods and data related to the Propellor ---
class PropCom(threading.Thread):
	CLOCKPERSEC = 80000000
	SYNCPERIOD = 80000000
	CLOCKERROR = 20000
	MIN_ADC_PERIOD = 8000
	nAvg = 1
	name = "?"
	com = None
	comOpen = False
	comlock = threading.Lock()
	ID = 0		# fixme (used to make a new ID for repeating timers) better way than counter? uuid? TODO
	msgID = 20
	lastMsgID = 0
	locks = dict() # dictionary of lock ID's -> timer objects (to keep track of active timers)
	eIDs = dict()

	# dictionary of callback functions for each 
	callbacks = dict()
	echoCallbacks = dict()


	# init function called on object creation. init's com and thread object
	def __init__ (self, callbacks=None):
		if callbacks is not None: self.callbacks = callbacks
		self.com = serial.Serial(timeout=None)
		threading.Thread.__init__(self)
		self.daemon = True
		self.setDaemon(True)
		self.lastPkt = 0
		self.lastTime = None
		self.lastRTime = 0
		self.cnt = 0
		self.MAXTICK = (1 << 32) -1
		self.port=None # initial port to attempt to open. overrides default search
		self.listeners = [set(),set(),set(),set(),set(),set(),set(),set()] # length 8 list of sets
	# starts the read loop in a seperate thread. all data is read into a buffer and parsed here. 
	def run(self):
		self.open(self.port)
		buf = EOP + " "
		waiting = 0
	
		while self.isOpen():
			# try to read in new info
			try:
				c = self.com.read(1)
				buf += c
				if c == EOP:
					c = self.com.read(1)
					buf += c
					buf = self.parse(buf)
			except serial.SerialException as err:
				logger.log("SerialException on read", err,logger.WARNING)
				self.close() # clean-up
				break
	# function that recreates the object.
	def restart(self):
		self.close()
		thread.sleep(1000)
		newSelf = PropCom(callbacks=self.callbacks)
		newSelf.start()
		return newSelf
	
	def onSync(self, tStamp):
		if self.lastTime is None:
			self.firstSyncTime = time.time()
			self.firstTime = tStamp
			self.lastTime = tStamp
			return
		#updates the clock counter with a new value. tests for overflow.
		if tStamp >= self.lastTime:
			elapsedTicks = tStamp - self.lastTime
			print "last: "  + str(self.lastTime) + " current: " + str(tStamp)
		else:
			elapsedTicks = tStamp + (self.MAXTICK - self.lastTime)
			print "!!last: "  + str(self.lastTime) + " current: " + str(tStamp)
		if elapsedTicks < self.SYNCPERIOD - self.CLOCKERROR:
			print "@#$%^&* ( sync too soon!! not enough ticks! )"
			print elapsedTicks
		if elapsedTicks > self.SYNCPERIOD + self.CLOCKERROR:
			print "@#$%^&* ( sync too late!! too many ticks! )"
			print elapsedTicks
	#	traceback.print_stack()

		self.cnt += elapsedTicks
		self.lastTime = tStamp
		print str(self.curTime()) + "seconds from first sync"
		if abs(self.curTime() - self.estTime()) > .5:
			print "!!!!!!!!!!!!!!!!!!!!!!!!!!!! Timing difference between curTime() and estTime() " + str(self.curTime() - self.estTime())
	def curTime(self):
		return (self.cnt) / float(self.CLOCKPERSEC)
	def estTime(self):
		return time.time()-self.firstSyncTime

	def realTime(self, tStamp):
		#returns the time, in seconds since the first sync, this timestamp should be. assuming it came AFTER the last sync.
		# this function acts like a sync. 
		# to avoid fake rollovers, time stamps must be prossesed in a linear order.
		#self.onSync(tStamp)

		
		if tStamp >= self.lastTime and tStamp - self.lastTime < self.MAXTICK/2: 			# this timestamp is after last sync, and no rollovers
			elapsedTicks = tStamp - self.lastTime
		elif self.lastTime - tStamp > self.MAXTICK/2: 	# this timestamp is new, but rolled over since last sync
			#print "!!" + str(self.lastTime) + "->" + str(tStamp)
			elapsedTicks = tStamp + (self.MAXTICK - self.lastTime)
		elif tStamp < self.lastTime:  						# this timestamp is slightly old, assuming it is not garbage data.
			elapsedTicks = tStamp - self.lastTime #returns a negative elapsed time.
		elif tStamp > self.lastTime and tStamp - self.lastTime > self.MAXTICK/2: #this timestamp is in the past, but clock recently rolled over.
			print "!!@" + str(self.lastTime) + "->" + str(tStamp)
			elapsedTicks = tStamp - self.MAXTICK - self.lastTime
		else:
			logger.log("No condition matched for 'realTime()'","Propellor.py", logger.ERROR)

		rTime = (self.cnt + elapsedTicks) / float(self.CLOCKPERSEC)
		if self.lastRTime > rTime:
			logger.log("Went back in time??? ("+str(self.lastTStamp)+"->"+str(tStamp)+") Dif="+str(self.lastTStamp-tStamp)+"ticks, " + str(self.lastRTime-rTime)+"seconds",rTime,logger.WARNING)
		self.lastTStamp = tStamp
		self.lastRTime = rTime


		return self.lastRTime
	# function that creates a new NONZERO ID. 
	def nextMsgID(self):
		self.msgID = (self.msgID + 1) & 255
		if self.msgID == 0:
			self.msgID = (self.msgID + 1) & 255
		return self.msgID
	# function that creates a new unique ID. 
	def newID(self):
		self.ID = (self.ID + 1)
		return self.ID

	# returns the name of channel idx. 
	#def channelName(self, idx):
	#	return self.name + " Channel " + str( idx )

	# function to add a listener to a stream. appends this listener to a list.
	def addListener(self, streamID, obj):
		self.listeners[streamID].add(obj)
	
	# function to remove a listener from a stream.
	def removeListener(self, streamID, obj):
		try:
			self.listeners[streamID].remove(obj)
		except KeyError as E:
			logger.log("No function registered in channel " + str(self.idx),  str(obj), logger.WARNING)
			raise


	# function to register a new callback for a certain key. appends new callback to a list. 
	def register(self, name, func, test=None):
		ID = self.newID()
		if name not in self.callbacks:
			self.callbacks[name] = dict()
		self.callbacks[name][ID]=(test, func)
		return ID
	# function to remove a function from the callback table 
	def deregister(self, name, funcID):
		try:
			rval = self.callbacks[name][funcID]
			del (self.callbacks[name])[funcID]
		except KeyError as E:
			rval = None
			logger.log("No function registered", name + ":" + str(funcID), logger.WARNING)
			raise

		return rval
	# open COM port for this prop. used to find prop waiting on ports
	def open(self, port=None):
		self.com.baudrate = DEFAULTBAUD
		def openPort(self, port):
			try:
				self.com.port = port
				self.com.open()
				logger.log("Opened port",self.com.port,logger.INFO)
				self.comOpen = True
			except Exception as e:
				self.comOpen = False
				logger.log("openPort Failed",e,logger.ERROR)
			time.sleep(3)
			self.send("version") # start the dialog
			return

		if port is None:
			self.openFirstProp(openPort) # opens the first com port
		else:
			openPort(self,port)
	def isOpen(self):
		return self.comOpen
	# closes COM port for this prop
	def close(self):
		comOpen = False
		self.send("stop",0) # stops all channels.
		self.com.close()
		# kill locks. 
		for idx,t in self.locks.iteritems():
			t.cancel()
			del self.locks[idx]


	# send a key to the prop		
	def send(self, key, value=None ):
		""" sends a control packet with a message ID that corresponds to the string value 'key', with parameters specified in value.
			key is a string that represents the message ID, or and int specifing the message ID.
			value is either an integer, or a list of integers."""
		

		if self.com is None or self.isOpen() == False:
			logger.log("send on bad port", key, logger.WARNING)
			return -1
	
		if key is None:
			logger.log("send NoneType key", key, logger.WARNING)
			return -1

		try:
			msg = chr(key) + chr(self.nextMsgID())
		except TypeError: # key is not an int. treat as string.			
			if key not in keyTable and key :
				logger.log("Attempting invalid control msg ID", key, logger.WARNING)
				return -1
			msg = chr(keyTable.index(key)) + chr(self.nextMsgID())

		if CTRLLOG:
			print msg
		if value is not None:
			try:
				for v in value:
					for n in range(4):
						msg += chr( (v>>24-n*8)&255 )
			except TypeError: # value is not a list. treat as int.
				for n in range(4):
					msg += chr( (int(value)>>24-n*8)&255 )
		msg = msg.replace(ESC, ESC+ESC)
		msg = msg.replace(EOP, ESC+EOP)
		chksum = 0
		for c in msg:
			chksum = ((chksum<<1) | (chksum>>7)) & 255 # left-rotate
			chksum = (chksum + ord(c)) % 256           # 8-bit addition
		msg = msg + EOP + chr(chksum)
		logger.log( "sending ", msg.replace("\a","@"), logger.INFO)
		self.comlock.acquire(True)	#block until lock taken	
		try:
			retv = self.com.write(msg)
		except (serial.serialutil.portNotOpenError, ValueError, serial.serialutil.SerialTimeoutException) as err:
			logger.log("Writing to closed port", err, logger.WARNING)
			return -1
		except serial.SerialException as err:
			logger.log("SerialException on write", err, logger.WARNING)
			return -1
		self.comlock.release()
		return 1 

		# parse all the keys in "resp". 
	def parse(self, msgBuffer ):
	  global DBG1
 	  DBG1=""
	  #find last EOP
	  n = 0
	  end = 0
	  
	  while not end == -1:
	    n = 0
	    escaped = 0
	    chksum = 0
	    chk = 0
	    state = 0
	    packet = ""
	    end = -1
	    
	    while end == -1:
	      if n == len(msgBuffer):
		end = -1
		DBG1+="X"
		break
	      c = msgBuffer[n]
	      n+=1
	      if state == 0: # finding first EOP
		if not escaped and c == EOP:
		  state = 1
		  DBG1+="{"
		else:
		  DBG1+="-"
	      elif state == 1: # checksum of last packet. useless.
		DBG1+="$("+str(ord(c))+")"
		chksum=0
		state = 2
	      elif state == 2: # collect packet data
		if not escaped and c == EOP:
		  DBG1+="}"
		  state = 3 #collect checksum
		elif escaped or (not c==ESC and not c==EOP):
		  packet+=c
		  DBG1+=c.replace("\a","@")
		  DBG1+="("+str(ord(c))+")"
		  DBG1+="."
		  chksum = ((chksum<<1) | (chksum>>7)) & 255 # left-rotate
		  chksum = (chksum + ord(c)) & 255           # 8-bit addition
	         
	        if c==ESC and not escaped:
		  DBG1+="/"
	  	  escaped = 1
		  chksum = ((chksum<<1) | (chksum>>7)) & 255 # left-rotate
		  chksum = (chksum + ord(c)) &255            # 8-bit addition
	        else:
		  escaped = 0 
	      elif state == 3: # storing checksum
		chk = ord(c)
		state = 2
		DBG1+="#"
		DBG1+="("+str(ord(c))+")"
		end = n
	    if PARSELOG:
		    print "parsed:[[" + DBG1.replace("\n","@").replace("\r","@") + "]]"
		
	    if end==-1:       
		    pass # no packets found.
	    else:
	      msgBuffer = msgBuffer[n-2:]
	      if  chk != chksum and chk!=0 and not IGNORECHKSUM:
		      if CTRLLOG:
			      print "BAD CHECKSUM!"
			      print "sent:"+str(chk)+" calculated:"+str(chksum)
	      else:
	        if len(packet) == 0:         
	          logger.log( "Bad Packet","No bytes!", logger.WARNING)
	        elif ord(packet[0]) & 128:
	          self.parseStream(packet)
	        else:
		  if MSGLOG:
	            logger.log("found",packet.replace("\a","@"),logger.INFO)
	          self.parseControl(packet)
	    
	  return msgBuffer
	  
	def parseStream(self, packet):
		''' parses a stream packet and passes parsed values to any registered stream listener objects'''
		c = ord(packet[0])
		streamID = (ord(packet[0])>>4) & 7
		#print c
		if STREAMLOG:
			logger.log("Stream ["+str(streamID)+"]","",logger.INFO)

		values = []
		val = 0
		valBits=32
		byteBits=4
		packet = chr(ord(packet[0])&15) + packet[1:]


		n=0

		for c in packet:
			c=ord(c)
			while byteBits>0:
				if valBits >= byteBits: # read in byteBits amount of bits
					val = (val<<byteBits) | c
					valBits -= byteBits
					byteBits = 0
				else: 			# read in valBits amount of bits, remaining bits left in c.
					val = (val<<valBits) | (c>>(byteBits-valBits))
					byteBits -= valBits
					c = c & (~(255<<valBits))
					valBits = 0
				if valBits <= 0:
					values.append(val)
					n+=1
					if STREAMLOG:
						print( "   :" + str(val)),
					val = 0
					if n<=1:
						valBits = 32
					else:
						valBits = 12
			byteBits = 8 # prepare for next byte
		self.callStream(streamID, values)

	  
	def parseControl(self, packet):
	  '''parses a control packet and calls any registered hooks for the packet's message ID type.'''
	  curVal = 0 
	  state = 0
	  nameNum = -1
	  n = 0
	  m = 0
	  exData = []
	 
	  while not n == len(packet):  
	    
	    c = packet[n]
	    n+=1      
	    if state == 0: #first byte: the message ID#
		nameNum = ord(c)
		state = 1
		
	    elif state == 1: #second byte: packet #
		self.lastPkt = ord(c)  
		state = 2
	    elif state == 2: #collect packet data
		curVal = curVal << 8
		curVal += ord(c)
		m += 1
		if m==4:
		  exData.append(curVal)
		  curVal = 0
		  m = 0
          if nameNum != 13 and CTRLLOG:
	    print("::" + str(nameNum) + "-" + str(self.lastPkt) + " = "),
	    for v in exData:
	      print(v),
	    print " "
	  self.call(nameNum, exData)
	  return  




	# call a function in the callback table. 
	def call(self, nameNum, val=None):
		global DBG1
		if nameNum<len(keyTable):
			name = keyTable[nameNum]
			if name in self.callbacks:
				for key, func in self.callbacks[name].items():
					try:
						if val is None or len(val)==0:
							if func[0] is None or func[0](self): #test validator
								func[1](self)
						elif func[0] is None or func[0](self, *val): #test validator
							func[1](self, *val)
					except Exception as e:
						dbugkey = name
						logger.log( "failed call -{ " + str(dbugkey) + " }- " , str(e), logger.INFO)
						logger.log( " debug",DBG1,logger.INFO)
		else:
			logger.log("bad control ID", nameNum, logger.WARNING)
	def callStream(self, streamID, values):
		if streamID>8:
			logger.log("Bad stream. StreamID too high!?", streamID, logger.ERROR)
			raise Exception("StreamID Too High!")

		for f in self.listeners[streamID].copy():
			try:
				f(self, values)
			except Exception as e:
				logger.log( "failed call -{ " + "stream[" + str(streamID) + "] }- ", e, logger.INFO)

	# find an open port with a propellor attached to it.
	def openFirstProp(self, openFunc):
		# store old version callback.
		if "version" in self.callbacks:
			oldVerCallback = self.callbacks["version"]
		else:	
			oldVerCallback = None
		del self.callbacks["version"]
		opened = [False]	# whether or not a valid port has been opened. 
		retry = True		# whether or not function will retry opening
		com = serial.Serial()
		#print "Baud Rate:" + str(self.com.baudrate)
		com.baudrate = self.com.baudrate
		#print "Baud Rate:" + str(com.baudrate)
		#print com.BAUDRATES
		#print com.getSettingsDict()


		while opened[0] == False and retry == True:
			# cycle through all available ports sending <version>, and waiting for response.
			ports = serial.tools.list_ports.comports()
			for p in ports:
				logger.log("Testing port",p[0], logger.INFO)
				com.port = p[0]
				ID = 0
				try:
					com.open()

					def verHandler(propCom,  ver):
						logger.log("Response on port",com.port,logger.INFO)
						if opened[0] == False:
							opened[0] = True
							com.close()	#make sure com is closed first
							openFunc(propCom, com.port)	#open new port
						return 0
					ID = self.register("version",verHandler)
				
					verStr = chr(3) + chr(1) + EOP + chr(7)
					self.comlock.acquire(True)	#block until lock taken	
					com.write(verStr)
					self.comlock.release()		#release comlock for others!	

					time.sleep(DEFAULTTIMEOUT)
					resp = com.read(com.inWaiting())
					if PARSELOG:
						print resp
					parsed = self.parse(EOP + " " + resp)
				except (serial.serialutil.SerialException, ValueError, serial.serialutil.SerialTimeoutException) as err: 
					logger.log("Error with port", com.port, logger.WARNING)
					com.close()
				finally:
					com.close() # make sure to close com port. 
					try:	# catch exceptions from invalid ID
						self.deregister("version",ID)
					except KeyError:
						logger.log("Can't Deregister version handler","ID does not exist", logger.WARNING)
					time.sleep(0.1)
			if opened[0] == False:
				retry = logger.ask("No Propeller detected. retry?", logger.QUESTION)
		
		if oldVerCallback is not None:
			self.callbacks["version"] = oldVerCallback
		else:
			del self.callbacks["version"] 
