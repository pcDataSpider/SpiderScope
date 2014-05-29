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

#function logger.write( String ) Write the string int the log as-is
def write( msg ):
	try:
		if printout == True:
			print msg
		if outFile != None:
			outFile.write( str(msg) + "\n" )
	except Exception as e:
		print "Error writing to log:" + str(e)
		pass

#function logger.log(String name, String options, Int mode) Add information to the log
# name = The message to be logged
# options = additional details about the message
# mode = specifies the logging level, 1-4, 1 being an error.
def log(name, options, mode=0):
	if mode == ERROR:
		write( "(E)" + name + ": " + str(options) )
	elif mode == WARNING:
		write( "(W)" + name + ": " + str(options) )
	elif mode == INFO:
		write( "(I)" + name + ": " + str(options) )
	else:
		write( "(?)" + name + ": " + str(options) )
	
#function logger.message(String message, Int mode) Display a message to the user in the form of a dialog box.
# message = The message to be displayed
# mode = The logging level, 1-4, 1 being a serious error
def message(message, mode=0):
	if mode == ERROR:
		wx.MessageBox(message, "Error", wx.OK | wx.ICON_ERROR)
	elif mode == WARNING:
		wx.MessageBox(message, "Warning", wx.OK | wx.ICON_EXCLAMATION)
	elif mode == INFO:
		wx.MessageBox(message, "Message", wx.OK | wx.ICON_INFORMATION)
	else:
		wx.MessageBox(message, "Message", wx.OK | wx.ICON_QUESTION)

#function  logger.ask(String message, Int mode) Ask the user a yes or no question
# message = the message to be displayed
# mode = The logging level, 1-4, 1 being a serious error
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

#function logger.trace() Print a stack trace
def trace():
	traceback.print_stack()
	


