import wx
import traceback

VERSION = 0.1   # global version number
ERROR = 1
WARNING = 2
INFO = 3
QUESTION = 4
outFile = None
printout = False
fName = "log.txt"

def write( msg ):
	try:
		if printout == True:
			print msg
		if outFile != None:
			outFile.write( str(msg) + "\n" )
	except Exception as e:
		print "Error writing to log:" + str(e)
		pass

def log(name, options, mode=0):
	if mode == ERROR:
		write( "(E)" + name + ": " + str(options) )
	elif mode == WARNING:
		write( "(W)" + name + ": " + str(options) )
	elif mode == INFO:
		write( "(I)" + name + ": " + str(options) )
	else:
		write( "(?)" + name + ": " + str(options) )
	
def message(message, mode=0):
	if mode == ERROR:
		wx.MessageBox(message, "Error", wx.OK | wx.ICON_ERROR)
	elif mode == WARNING:
		wx.MessageBox(message, "Warning", wx.OK | wx.ICON_EXCLAMATION)
	elif mode == INFO:
		wx.MessageBox(message, "Message", wx.OK | wx.ICON_INFORMATION)
	else:
		wx.MessageBox(message, "Message", wx.OK | wx.ICON_QUESTION)

def ask(message, mode=4):
	if mode == ERROR:
		ret = wx.MessageBox(message, "Error", wx.YES_NO | wx.ICON_ERROR)
	elif mode == WARNING:
		ret = wx.MessageBox(message, "Warning", wx.YES_NO | wx.ICON_EXCLAMATION)
	elif mode == INFO:
		ret = wx.MessageBox(message, "Message", wx.YES_NO | wx.ICON_INFORMATION)
	elif mode == QUESTION:
		ret = wx.MessageBox(message, "Message", wx.YES_NO | wx.ICON_QUESTION)
	else:
		ret = wx.MessageBox(message, "Message", wx.YES_NO | wx.ICON_QUESTION)
	if ret == wx.YES:
		return True
	else:
		return False

def trace():
	traceback.print_stack()
	


