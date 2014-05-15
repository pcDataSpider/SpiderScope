import Queue
import wx
import wx.lib.plot
import logger
import time
import threading
import os


colorTable = [ "blue", "red", "green", "yellow", "purple", "black" ]


class GetNumBox(wx.Dialog):
	def __init__(self, parent, xRange = None, prompt="Number", title="Num", text=""):
		wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title = "Enter A Number")





class GraphInfoBox(wx.Dialog):
	def __init__(self, parent, xRange=(0,100), yRange=(0,100), xmin=0, xmax=99999999, ymin=0, ymax=4096, xunits="Seconds", yunits="units"):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = "Graph Information"  )
		ico = wx.Icon('OFSI-Logo.ico', wx.BITMAP_TYPE_ICO )
		self.SetIcon( ico )
		xcheck = False
		ycheck = False
		if xRange is None:
			xcheck = True
			xRange = (0,0)
		if yRange is None:
			ycheck = True
			yRange = (0,0)
		# -- create window controls --
		self.mainSizer = wx.BoxSizer( wx.VERTICAL )
		self.mainSizer.AddSpacer( ( 0, 10), 0, wx.EXPAND, 5 )
		txt2 = wx.StaticText( self, wx.ID_ANY, "Graph Dimensions:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.mainSizer.Add( txt2, 0, wx.LEFT|wx.TOP, 10 )
		
		axisSplit = wx.BoxSizer( wx.HORIZONTAL )
		xSizer = wx.BoxSizer( wx.VERTICAL )
		ySizer = wx.BoxSizer( wx.VERTICAL )
		axisSplit.Add( xSizer, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 15)
		axisSplit.Add( ySizer, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 15)
		self.mainSizer.Add(axisSplit, 0, wx.ALL, 5)

		# add controls for x axis
		xdimSizer = wx.BoxSizer( wx.HORIZONTAL )
		self.xLower = wx.TextCtrl( self, wx.ID_ANY, str(xRange[0]), wx.DefaultPosition, wx.Size( 45,-1 ), 0 )
		self.xUpper = wx.TextCtrl( self, wx.ID_ANY, str(xRange[1]), wx.DefaultPosition, wx.Size( 45,-1 ), 0 )
		xtxt2 = wx.StaticText( self, wx.ID_ANY, " - " , wx.DefaultPosition, wx.DefaultSize, 0 )
		xdimSizer.Add( self.xLower, 1, wx.BOTTOM, 5 )
		xdimSizer.Add( xtxt2, 0, 0, 5 )
		xdimSizer.Add( self.xUpper, 1, wx.BOTTOM, 5 )

		if xunits is not None:
			xtitle = "X Axis (" + xunits + ") :"
		else:
			xtitle = "X Axis :"
		xtxt = wx.StaticText( self, wx.ID_ANY, xtitle , wx.DefaultPosition, wx.DefaultSize, 0 )

		self.xautoScale = wx.CheckBox(self, wx.ID_ANY, "Autoscale", wx.DefaultPosition, wx.DefaultSize, 0)
		self.xautoScale.SetValue(xcheck)

		xSizer.Add(xtxt, 0, wx.ALL, 5)
		xSizer.Add(xdimSizer, 0, wx.ALL, 5)
		xSizer.Add(self.xautoScale, 0, wx.LEFT, 10)

		# add controls for y axis
		ydimSizer = wx.BoxSizer( wx.HORIZONTAL )
		self.yLower = wx.TextCtrl( self, wx.ID_ANY, str(yRange[0]), wx.DefaultPosition, wx.Size( 45,-1 ), 0 )
		self.yUpper = wx.TextCtrl( self, wx.ID_ANY, str(yRange[1]), wx.DefaultPosition, wx.Size( 45,-1 ), 0 ) 
		ytxt2 = wx.StaticText( self, wx.ID_ANY, " - " , wx.DefaultPosition, wx.DefaultSize, 0 )
		ydimSizer.Add( self.yLower, 1, wx.BOTTOM, 5 )
		ydimSizer.Add( ytxt2, 0, wx.BOTTOM, 5 )
		ydimSizer.Add( self.yUpper, 1, wx.BOTTOM, 5 )

		if yunits is not None:
			ytitle = "Y Axis (" + yunits + ") :"
		else:
			ytitle = "Y Axis :"
		ytxt = wx.StaticText( self, wx.ID_ANY, ytitle , wx.DefaultPosition, wx.DefaultSize, 0 )

		self.yautoScale = wx.CheckBox(self, wx.ID_ANY, "Autoscale", wx.DefaultPosition, wx.DefaultSize, 0)
		self.yautoScale.SetValue(ycheck)
		ySizer.Add(ytxt, 0, wx.ALL, 5)
		ySizer.Add(ydimSizer, 0, wx.ALL, 5)
		ySizer.Add(self.yautoScale, 0, wx.LEFT, 10)

	

		# add OK/Cancel button controls
		#btnSizer = self.CreateButtonSizer( wx.OK | wx.CANCEL )
		btnSizer = wx.BoxSizer( wx.HORIZONTAL )
		okBtn = wx.Button( self, wx.ID_ANY, "OK", wx.DefaultPosition, wx.DefaultSize, 0 )
		cancelBtn = wx.Button( self, wx.ID_ANY, "Cancel", wx.DefaultPosition, wx.DefaultSize, 0 )
		btnSizer.Add( okBtn, 1, wx.ALIGN_RIGHT, 5 )
		btnSizer.Add( cancelBtn, 1, wx.ALIGN_RIGHT, 5 )
		self.mainSizer.Add( btnSizer, 1, wx.ALIGN_RIGHT, 5 )
		# set default buttons
		self.SetAffirmativeId(okBtn.GetId())
		self.SetEscapeId(cancelBtn.GetId())
		
		self.SetSizer( self.mainSizer )
		self.Layout()
		self.Fit()
		
		self.Centre( wx.BOTH )
		self.On_X_Autoscale(None)
		self.On_Y_Autoscale(None)

		# -- Connect Events --
		self.xautoScale.Bind( wx.EVT_CHECKBOX, self.On_X_Autoscale )
		self.yautoScale.Bind( wx.EVT_CHECKBOX, self.On_Y_Autoscale )
		okBtn.Bind( wx.EVT_BUTTON, self.On_OK )
		cancelBtn.Bind( wx.EVT_BUTTON, self.On_Cancel )
		self.Bind( wx.EVT_CLOSE, self.On_Close )
	def On_Y_Autoscale(self, event):
		enabled = not self.yautoScale.GetValue()
		self.yLower.Enable( enabled )
		self.yUpper.Enable( enabled )
	def On_X_Autoscale(self, event):
		enabled = not self.xautoScale.GetValue()
		self.xLower.Enable( enabled )
		self.xUpper.Enable( enabled )

	def On_Close(self, event):
		self.EndModal(wx.ID_CANCEL)
		pass	

	def On_Cancel(self, event):
		self.EndModal(wx.ID_CANCEL)

	def On_OK(self, event):
		if self.xautoScale.GetValue():
			self.xRange = None
		else:
			try:
				self.xMin = float(self.xLower.GetValue())
			except ValueError:
				self.xMin = 0
			try:
				self.xMax = float(self.xUpper.GetValue())
			except ValueError:
				self.xMin = 0
				self.xMax = 0
			self.xRange = (self.xMin, self.xMax )

		if self.yautoScale.GetValue():
			self.yRange = None
		else:
			try:
				self.yMin = float(self.yLower.GetValue())
			except ValueError:
				self.yMin = 0
			try:
				self.yMax = float(self.yUpper.GetValue())
			except ValueError:
				self.yMin = 0
				self.yMax = 0
			self.yRange = (self.yMin, self.yMax )


		self.EndModal(wx.ID_OK)
	

	


	
class GraphFrame(wx.Frame):
	def __init__(self, parent, xRange=None, yRange=None, xSize=None, ySize=None, nPoints=None, header=None,  title="Graph", xlabel="Seconds", ylabel="Value", showPoints=False, POINTDEBUG=False):
		self.max_X = xSize
		self.max_Y = ySize
		self.xRange = xRange
		self.yRange = yRange
		self.nPoints = nPoints
		self.showPoints = showPoints
		self.POINTDEBUG = POINTDEBUG



		if self.nPoints is not None:
			self.dataQueue = Queue.Queue(self.nPoints)

		self.title = title
		self.xlabel = xlabel
		self.ylabel = ylabel
		self.outFile = None
		self.header = header
		if self.header is None:
			date = '"' + time.asctime() + '"'
			self.header = date

		wndsize = wx.Size(500,500)

		self.pending = False

		# initialize frame object
		wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=self.title , pos=wx.DefaultPosition, size=wndsize)
		ico = wx.Icon('OFSI-Logo.ico', wx.BITMAP_TYPE_ICO )
		self.SetIcon( ico )

		# add menubar
		self.menuBar = wx.MenuBar( 0 )
		self.fileMenu = wx.Menu()
		self.editMenu = wx.Menu()
		self.menuBar.Append(self.fileMenu, "File")
		self.menuBar.Append(self.editMenu, "Edit")
		# create menu items
		save = wx.MenuItem( self.fileMenu, wx.ID_ANY, "Save", "Saves the current graph", wx.ITEM_NORMAL )
		close = wx.MenuItem( self.fileMenu, wx.ID_ANY, "Close", "Closes the graph window", wx.ITEM_NORMAL )
		setAxis = wx.MenuItem( self.fileMenu, wx.ID_ANY, "Dimensions", "Changes the graph dimensions", wx.ITEM_NORMAL )
		# append menu items
		self.fileMenu.AppendItem(save)
		self.fileMenu.AppendItem(close)
		self.editMenu.AppendItem(setAxis)
		# bind items
		self.Bind( wx.EVT_MENU, self.OnClose, id=close.GetId() )
		self.Bind( wx.EVT_MENU, self.OnResize, id=setAxis.GetId() )
		self.Bind( wx.EVT_MENU, self.OnSave, id=save.GetId() )
		self.SetMenuBar( self.menuBar)
	
		# add plot
		self.mainSizer = wx.BoxSizer(wx.VERTICAL)
		self.plot = wx.lib.plot.PlotCanvas(self, size=wx.Size(500,500), style=wx.EXPAND)
		self.plot.SetShowScrollbars(True)

		# add points
		self.data = dict()
		self.displayData = dict()
		if self.max_X is not None:
			lastX = self.max_X/2.0 
		elif self.xRange is not None:
			lastX = xRange[0]
		else:
			lastX = 0
		if self.max_Y is not None:
			lastY = self.max_Y/2.0
		elif self.yRange is not None:
			lastY = yRange[0]
		else:
			lastY = 0

		self.lastpoint = (lastX, lastY)
		self.updateTimer = None

		self.mainSizer.Add(self.plot, 1, wx.EXPAND, 0)
		self.SetSizer(self.mainSizer)
		self.Layout

		self.Bind(wx.EVT_CLOSE,self.OnClose)

	

	def updateData(self):

		lines = []
		if not self.data:
			lines.append( wx.lib.plot.PolyLine([self.lastpoint], colour="black", width=1) )
		else:
			n = 0
			for idx in self.data:
				thisColor = colorTable[n]
				n += 1
				if self.showPoints:
					if self.nPoints > 0:
						lines.append( wx.lib.plot.PolyMarker(self.displayData[idx], colour=thisColor, width=2, fillstyle=wx.SOLID, fillcolour=thisColor, size=1, marker="circle") )
					else:
						lines.append( wx.lib.plot.PolyMarker(self.data[idx], colour=thisColor, width=2, fillstyle=wx.SOLID, fillcolour=thisColor, size=1, marker="circle") )
				if self.nPoints > 0:
					lines.append( wx.lib.plot.PolyLine(self.displayData[idx], colour=thisColor, legend=str(idx), width=1) )
				else:
					lines.append( wx.lib.plot.PolyLine(self.data[idx], colour=thisColor, legend=str(idx), width=1) )
				#lines.append( wx.lib.plot.PolyLine(self.dataQueue, colour="green", width=1) )
		pg = wx.lib.plot.PlotGraphics(lines, self.title, self.xlabel, self.ylabel)
		if self.max_X is not None:
			self.xRange = ( self.lastpoint[0] - self.max_X/2.0, self.lastpoint[0] + self.max_X/2.0 )
		if self.max_Y is not None:
			self.yRange = ( self.lastpoint[1] - self.max_Y/2.0, self.lastpoint[1] + self.max_Y/2.0 )
		
		if len( self.data ) > 1 :
			self.plot.SetEnableLegend(True)
		self.plot.Draw(pg, self.xRange, self.yRange)
		self.pending = False
		
	
	def addPoint(self, x, y, idx, debugObj=None):
		if idx not in self.data:
			self.data[idx] = []
			self.displayData[idx] = []
		self.data[idx].append((x,y,debugObj))
		self.displayData[idx].append((x,y))
		#if self.dataQueue.full():
		#	self.dataQueue.get()
		#self.dataQueue.put((x,y))
		#if self.nPoints > 0:
		#	self.xRange = 
		if self.nPoints > 0:
			tPoints = 0
			for c in self.displayData:
				tPoints += len( self.displayData[c] )

			if tPoints > self.nPoints:
				self.displayData[idx].pop(0)

		self.lastpoint = (x,y)
		if not self.pending:
			self.pending = True
			def update():
				self.updateData()
			self.updateTimer = threading.Timer(.5,update)
			self.updateTimer.start()
	def OnResize(self, event):
		info = GraphInfoBox(self, xRange=self.xRange, yRange=self.yRange, xunits=self.xlabel, yunits=self.ylabel) 
		if info.ShowModal() == wx.ID_OK:
			self.xRange = info.xRange
			self.yRange = info.yRange
		self.updateData()

	def OnSave(self, event):
		filetypes = "CSV files (*.csv)|*.csv|Text files (*.txt)|*.txt|All files|*"
		dlg = wx.FileDialog(self, "Choose a file", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT, wildcard=filetypes)
		outFile = None
		if dlg.ShowModal()==wx.ID_OK:
			try:
				filename=dlg.GetFilename()
				dirname=dlg.GetDirectory()
				fullPath = os.path.join(dirname, filename)	
				self.SetTitle( self.title + " - " + filename )
				outFile = open(fullPath, "w")
				# write header info
				outFile.write( self.header )
				outFile.write( "\n" )
				for idx in self.data:
					outFile.write(", X" + str(idx) )
					outFile.write(", Y" + str(idx) )
					if self.POINTDEBUG:
						outFile.write(", DEBUG" + str(idx) )
				outFile.write( "\n" )
				# write data
				nData = 0
				for idx in self.data:
					if len(self.data[idx]) > nData:
						nData = len( self.data[idx] )
				for n in range( nData ):
					for idx in self.data:
						try:
							strfmt = ",{0:.5f},{1}".format(self.data[idx][n][0], self.data[idx][n][1])
							if self.POINTDEBUG:
								strfmt += "," + str(self.data[idx][n][2])
							outFile.write(strfmt)
						except IndexError:
							pass
					outFile.write( "\n")
				outFile.close()
			except IOError as e:
				logger.log("Error opening file", e, logger.WARNING)
				logger.message("Error opening file.", logger.ERROR)
			except ValueError as e:
				logger.log("Error writing file", e, logger.WARNING)
				logger.message("Error writing file.", logger.ERROR)
		dlg.Destroy()



	def OnClose(self, event):
		if self.updateTimer is not None: self.updateTimer.cancel()
		self.Destroy()

