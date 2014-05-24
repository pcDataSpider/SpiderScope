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
DEFAULTTIMEOUT = 5.5	# Timeout for propellor to respond
DEFAULTREADSLEEP = 0.1 	# Time that the read loop sleeps for. 
DEFAULTFLUSH = 1 	# Interval to flush channel data 
DEFAULTOUTFILE = "test.txt"
MAX_EID = 200
MSG_HEAD = 2
VERNUM = 10		# version 1.0
PARSELOG = True #enable logging the entire message parsing algorithm. handy to see COM port buffer state.
MSGLOG = True #enable logging every message. 

p_key = re.compile("""<(([^<>@:]+?))(:((([^<>'",#$:]*)|(#.{4})|(\$.{2})|(['"].*?['"])),)*(([^<>'",#$:]*)|(#.{4})|(\$.{2})|(['"].*?['"]))?)?>""", re.DOTALL)  # Matches Any Key!
p_wholename = re.compile("<[^@:]*?[:]", re.DOTALL) # matches the entire name including <..|...:  (must have value field)
p_name = re.compile("<[^@:]*?[:>]", re.DOTALL) # matches only the name of the key including "< ... :" (no echo) 
p_wholeval = re.compile(""":(((['"][^'"]*['"])|(#.{4})|(\$.{2})|([^<>'",#$:]*)),)*((#.{4})|(\$.{2})|([^<>"',#$:]*)|(['"][^'"]*['"]))?>""", re.DOTALL) # matches only the value of the key including ": ... >"
p_val = re.compile("""(((['"][^'"]*['"])|(#.{4})|(\$.{2})|([^<>'",#$:]*)),)|(((['"][^'"]*['"])|(#.{4})|(\$.{2})|([^<>'",#$:]*))>)""", re.DOTALL) # matches only a single value of the value fiel



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

		#def flushChannels():
		#	for key, c in self.channels.iteritems():
		#		c.flush()
		#t = RepeatTimer.Timer(DEFAULTFLUSH, flushChannels)
		#t.start()


	#query prop about the state of a certain channel
	def queryChannel(self, chan=None):
		global prop
		if chan is None:
			for x in self.analogIn:
				idx = self.channels[x].idx
				self.propCom.send("set", idx)
			for x in self.analogOut:
				idx = self.channels[x].idx
				self.propCom.send("set", idx)
			idx = self.digitals.idx
			self.propCom.send("set", idx)
			self.propCom.send("dir")
			self.propCom.send("start")
		else:
			if chan in self.channels:
				idx = self.channels[chan].idx
				self.propCom.send("set", idx)
				self.propCom.send("type", idx)
			else:
				logger.log("Bad Channel Querry", chan, logger.WARNING)
			self.propCom.send("start")	





# --- The communication object. Represents methods and data related to the Propellor ---
class PropCom(threading.Thread):
	CLOCKPERSEC = 80000000
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
	# starts the read loop in a seperate thread. all data is read into a buffer and parsed here. 
	def run(self):
		self.open()
		buf = ""
		waiting = 0
	
		while self.isOpen():
			# try to read in new info
			try:
				buf += self.com.read(1)
				buf = self.parse(buf)
			except serial.SerialException as err:
				logger.log("SerialException on read", err,logger.WARNING)
				self.close() # clean-up
				break
	# function that recreates the object.
	def restart(self):
		self.close()
		newSelf = PropCom(callbacks=self.callbacks)
		newSelf.start()
		return newSelf
	
	# function that creates a new unique ID. 
	def nextMsgID(self):
		self.msgID = (self.msgID + 1) & 255
		while self.msgID == 0:
			self.msgID = (self.msgID + 1) & 255
		return self.msgID
	# function that creates a new unique ID. 
	def newID(self):
		self.ID = (self.ID + 1)
		return self.ID

	# returns the name of channel idx. 
	#def channelName(self, idx):
	#	return self.name + " Channel " + str( idx )

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
			self.send("version") # start the dialog
			self.send("nchannels")
				
			return

		if port is None:
			self.openFirstProp(openPort) # opens the first com port
		else:
			openPort(port)
	def isOpen(self):
		return self.comOpen
	# closes COM port for this prop
	def close(self):
		comOpen = False
		self.send("stop","0") # stops all channels.
		self.com.close()
		# kill locks. 
		for idx,t in self.locks.iteritems():
			t.cancel()
			del self.locks[idx]


	# send a key to the prop		
	def send(self, key, value=None ):
		

		if self.com is None or self.isOpen() == False:
			logger.log("send on bad port", key, logger.WARNING)
			return -1
	
		if key is None:
			logger.log("send NoneType key", key, logger.WARNING)
			return -1

		msg = key
		if value is not None:
			msg += ":"
			if isinstance( value, list ):
				tmpval = ""
				for i in value:
					i=str(i)
					try:
						i=int(i)
						if i>9999:
							tmp=""
							mask = 255
							for n in range(4):
								tmp+= chr( (i & mask) >> 8 * n)
								mask = mask << 8
							tmp+="#"
							i = tmp[::-1]
									
					except ValueError:
						i="'"+i+"'"
					tmpval = tmpval + str(i) + ","
					
				value = tmpval[:-1] # crop off last ','

			else:
				value=str(value)
				try:
					value=int(value)
					if value>9999:
						tmp=""
						mask = 255
						for n in range(4):
							tmp+= chr( (value & mask) >> 8 * n)
							mask << 8
						tmp+="#"
						value = tmp[::-1]
					else:
						value = str(value)
								
				except ValueError:
					value="'"+str(value)+"'"
			msg += value



	
		msg = "<" + msg + ">"

		logger.log( "sending ", msg.replace("\a","#"), logger.INFO)
		self.comlock.acquire(True)	#block until lock taken	
		try:
			retv = self.com.write(msg)
		except (serial.serialutil.portNotOpenError, ValueError, serial.serialutil.SerialTimeoutException) as err:
			logger.log("Writing to closed port", err, logger.WARNING)
		except serial.SerialException as err:
			logger.log("SerialException on write", err, logger.WARNING)
		self.comlock.release()
		return 
	# parse all the keys in "resp". 
	def parse(self, resp):
		#simply start the recursion of parseKey
		printkey = resp
		printkey.replace('\a','~') # printable version of string with no audible bells
		if PARSELOG:
			sys.stdout.write("{|" + printkey + "|} \n " )
		if MSGLOG:
			key = p_key.search(resp)	
			if key is not None:
				logger.log(printkey, "|", logger.INFO)
		val = self.parseKey(resp)
		if PARSELOG:
			print "    ^ Done parsing."
		return val
	# recursively parses the string, "keys" until there are no more keys to 
	def parseKey(self, keys):
		#printkey = keys
		#printkey.replace('\a','@') # printable version of string with no audible bells

		key = p_key.search(keys)	
		#prop.send("channel",prop.channel.idx)
		if key is None:
			#print printkey + " || " + printkey
			#if PARSELOG:
			#	print printkey + "  |} "
			return keys

		keystr = key.group()
		if keystr is None:
			#if PARSELOG:
			#	print printkey + " |} "
			logger.log("regex error", "matched, but no result", logger.WARNING)
			return keys
		if len(keystr) < 5:
			logger.log("short msg", keys, logger.WARNING)
			return keys

		printkey = keystr
		printkey = printkey.replace('\a','!') # printable version of string with no audible bells  <...!name:vals>
		if PARSELOG:
			print printkey
		name = p_wholename.search(keystr)

		if name is None: # check if this key is a query. if so there is no ':'
			name = keystr[1:-1]
			val = None
		else: # this key has a valid value field.
			name = name.group()[1:-1]

			val =  p_wholeval.search(keystr)
			if val is None:
				val = []
			else:
				val = val.group()[1:]
				val = self.parseVal(val)

		self.call(name,printkey ,val, )

		#if PARSELOG:
			#sys.stdout.write(printkey + " -> ")
		#retval = self.parseKey(keys[:key.start()] + keys[key.end():])
		retval = self.parseKey(keys[key.end():])
		return retval

	# parses the value part of a message and returns a list of real values. numbers, or strings. 
	def parseVal(self, valstr):
		vList = []
		done = False
		while not done:
			val = p_val.search(valstr)
			if val is None:
				done = True
			else:
				valstr = valstr[val.end():]
				val =  val.group()[:-1]
				#look at first letter.
				if len(val)==5 and val[0] == "#": # binary type
					val = val[1:]  # gives only the 4 bytes we are interested in
					tmp = 0
					for n in range(4): # shift and add in each character
						tmp = (tmp<<8) + ord(val[n])
					val = tmp
				elif len(val)==3 and val[0] == "$": # sum type
					val = val[1:]  # gives only the 2 bytes we are interested in
					tmp = 0
					for n in range(2): # shift and add in each character
						tmp = (tmp<<8) + ord(val[n])
					val = tmp
						
				elif len(val) >= 1 and (val[0] == '"' or val[0] == "'"): # string type
					val = val[1:-1]
				else: # number/string type
					try:
						vtmp = int(val) # TODO will vtmp be written to on failure?
					except ValueError:
						vtmp = val
					val = vtmp
					
				
				vList.append(val)
		return vList

	# call a function in the callback table. 
	def call(self, name, dbugkey, val=None):
		if name in self.callbacks:
			for key, func in self.callbacks[name].items():
				try:
					if val is None or len(val)==0:
						if func[0] is None or func[0](self):
							func[1](self)
					elif func[0] is None or func[0](self, *val):
						func[1](self, *val)
				except Exception as e:
					logger.log( "failed call -{ " + str(dbugkey) + " }- " , str(e), logger.INFO)



	# find an open port with a propellor attached to it.
	def openFirstProp(self, openFunc):
		# store old version callback.
		if "version" in self.callbacks:
			oldVerCallback = self.callbacks["version"]
		else:	
			oldVerCallback = None
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
				
					self.comlock.acquire(True)	#block until lock taken	
					com.write("<version>")
					self.comlock.release()		#release comlock for others!	

					time.sleep(DEFAULTTIMEOUT)
					resp = com.read(com.inWaiting())
					parsed = self.parse(resp)
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
