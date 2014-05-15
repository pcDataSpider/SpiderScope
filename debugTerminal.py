
import sys
import os
import imp
import wx
import GUI3
import Propeller
import serial
import threading
import RepeatTimer

import logger

# imports for plugins (for compiling)

import Queue
import wx.lib.plot
import wx.lib.scrolledpanel as scrolled
import graph
import pickle


nChannels = 4
nAnalogI = 4
nAnalogO = 2
nDigitals = 8

device = None
import serial

LOGFILE = True
PRINTOUT = True
POINTDEBUG = False
DEBUGDIALOG = False

def main():
	# start logger
	if LOGFILE:
		logger.outFile = open( logger.fName, "w" )
	logger.printout = PRINTOUT

	# setup propeller object
	propCom = Propeller.PropCom()
	propCom.POINTDEBUG = POINTDEBUG

	# define message handlers
	def versionHandler(propCom,  ver):
		logger.log("Propeller version", ver, logger.INFO)
		device.queryChannel()

	def syncHandler(propCom, time, overflow=0):
		propCom.onSync(time)

	def dbgHandler(propCom, v1=None, v2=None, v3=None, v4=None, v5=None):
		strFmt = "Debug Message:\n"
		strFmt += str(v1) + "\n"
		strFmt += str(v2) + "\n"
		strFmt += str(v3) + "\n"
		strFmt += str(v4) + "\n"
		strFmt += str(v5) + "\n"
		logger.message(strFmt)
			


	#device.propCom.register("info", nchannelsHandler)
	propCom.register("version", versionHandler)
	if DEBUGDIALOG:
		propCom.register("over", dbgHandler)
	propCom.register("sync", syncHandler)


	#device.propCom.start()	# start prop, begins polling open ports
	# ask usr for port name
	for p in serial.tools.list_ports.comports():
		print p
	print "open which port?"
	PORT = raw_input()
	propCom.port=PORT
	propCom.start()

	while True:
		print "nameNum="
		nameNum = raw_input()
		print "nArgs="
		nArgs = int(raw_input())
		args=[]
		for n in range(nArgs):
			print "arg " + str(n) + "="
			args.append(int(raw_input()))
		propCom.send(nameNum,args)
	# setup complete, show frame. 

	# program termination.  
	propCom.close()
	if LOGFILE:
		logger.outFile.close()

# start program
main()
