#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
Written by Ethan Shaw
"""

import Tkinter, tkMessageBox, tkFileDialog, os, sys
from tkColorChooser import askcolor
from PIL import ImageTk
import ScienceFairProcess

class TKMixInClass:

	# we take app as an argument, which inherits from Tkinter.Tk
	def __init__(self, app):
		self.app = app

	################################################################################
	#
	# GUI utility methods
	#
	################################################################################
	def addTextEntry(self, textvariable, row, column, command):
		entry = Tkinter.Entry(self.app, textvariable=textvariable)
		entry.grid(column=column,row=row,sticky='EW')
		entry.bind("<Return>", command)
		return entry
		
	def addButton(self, row, column, title, command):
		button = Tkinter.Button(self.app, text=title, command=command)
		button.grid(column=column,row=row)
		return button

	def addCanvas(self, row, column, columnspan, width, height):
		frame = Tkinter.Frame(self.app)
		frame.grid(row=row,column=column,columnspan=columnspan, sticky="n")
		canvas = Tkinter.Canvas(frame, bg="black", width=width, height=height)
		canvas.pack()
		
		return canvas
	
	def addOptionsMenu(self, textvariable, choices, defaultchoice, row, column):
		self.setStringVariableValue(textvariable, defaultchoice)
		menu = apply(Tkinter.OptionMenu, (self.app, textvariable) + tuple(choices))
		menu.grid(column=column,row=row)
		return menu
	
	def addColorButton(self, row, column, title):
		return self.addButton(row, column, title, askcolor)
	
	def addImageToCanvas(self, canvas, image):
		try:
			photoimage = ImageTk.PhotoImage(file=image)
			canvas.delete("all")
			canvas.create_image(150, 150, image=photoimage)
		except:
			print "Error opening file"
		
	def showInfoMessage(self, message):
		tkMessageBox.showinfo("Information", message)
	
	def showErrorMessage(self, message):
		tkMessageBox.showinfo("Error", message)
		
	def openFileDialog(self):
		return tkFileDialog.askopenfile(mode='r')
	
	def getExistingFilePath(self):
		return tkFileDialog.askopenfilename()	 
	
	# All GUI items seem to have a 'textvariable' (type Tkinter.StringVar)
	# if you set this then you can change the value by using set and get
	def setStringVariableValue(self, variable, string):
		variable.set(string)
	
	def setIntVariableValue(self, variable, value):
		variable.set(value)
	
	def getStringVariableValue(self, variable):
		return variable.get()

	def addLabel(self, row, column, columnspan, textvariable, value):
		# anchor="w" means that the text should be left aligned in the label
		label = Tkinter.Label(self.app, textvariable=textvariable, anchor="w", fg="black", bg="white")
		label.grid(column=column,row=row,columnspan=columnspan,sticky='EW')
		
		if ( value ):
			self.setStringVariableValue(textvariable, value)
		
		return label
	
	def addCheckBox(self, row, column, textvariable, variable, value):
		self.setIntVariableValue(variable, value)
		checkbox = Tkinter.Checkbutton(self.app, textvariable=textvariable, variable=variable)
		checkbox.grid(column=column,row=row,sticky='EW')
		return checkbox
	
	def getFile(self):
		path = self.getExistingFilePath()
		self.setStringVariableValue(self.filePathEntry, path)
		
	def deleteRow(self):
		if ( self.app.fileChoosers != None ):
			for chooser in self.app.fileChoosers:
				if chooser == self:
					self.app.fileChoosers.remove(self)
					self.destroy()
					return
		print "Didn't find", self


class FileChooserRow(TKMixInClass):
	def __init__(self, app, row=0, column=0, columnspan=1, startcolor="red"):
		TKMixInClass.__init__(self, app)
		
		# set columns for items
		chooseLabelColumn = column
		pathEntryColumn = (column + columnspan)
		chooseButtonColumn = (pathEntryColumn + 1)
		colorButtonColumn = chooseButtonColumn + 1
		preprocessColumn = colorButtonColumn + 1
		deleteRowButtonColumn = preprocessColumn + 1
		
		self.chooseLabelText = Tkinter.StringVar()
		self.chooseLabel = self.addLabel(textvariable=self.chooseLabelText, row=row, column=chooseLabelColumn, columnspan=columnspan, value="Choose A File")
		self.app.grid_columnconfigure(chooseLabelColumn,weight=0)
		
		self.filePathEntry = Tkinter.StringVar()
		self.pathEntry = self.addTextEntry(textvariable=self.filePathEntry, row=row, column=pathEntryColumn, command=None)
		
		self.app.grid_columnconfigure(pathEntryColumn,weight=1)
		
		self.chooseButton = self.addButton(row, column=chooseButtonColumn, title="Choose", command=self.getFile)
		
		self.outlierCheckLabel = Tkinter.StringVar()
		self.outlierCheckLabel.set("Remove Outliers")
		self.outlierCheckVar = Tkinter.IntVar(self.app)
		self.outlierCheckBox = self.addCheckBox(row, column=preprocessColumn, textvariable=self.outlierCheckLabel, variable=self.outlierCheckVar, value=1)
		
		colors = ['red', 'green', 'blue']
		self.optionsColor = Tkinter.StringVar()
		self.setStringVariableValue(self.optionsColor, startcolor)
		self.colorMenu = self.addOptionsMenu(textvariable=self.optionsColor, choices=colors, defaultchoice=startcolor, row=row, column=colorButtonColumn)
		self.deleteRowButton = self.addButton(row, column=deleteRowButtonColumn, title="Delete Row", command=self.deleteRow)
	
	def getExistingFilePath(self):
		return tkFileDialog.askopenfilename()
		
	def getFileAndColorAndFlags(self):
		flags = { "preprocess" : self.outlierCheckVar.get() }
		return (self.filePathEntry.get(), self.optionsColor.get(), flags)
		
	def destroy(self):
		self.chooseLabel.destroy()
		self.pathEntry.destroy()
		self.chooseButton.destroy()
		self.colorMenu.destroy()
		self.deleteRowButton.destroy()
		self.outlierCheckBox.destroy()

class FITSImageProcessorApp(Tkinter.Tk, TKMixInClass):
	def __init__(self, parent):
		Tkinter.Tk.__init__(self, parent) # self is the root Tk()
		TKMixInClass.__init__(self, self)
		self.parent = parent
		self.initialize()
	
	def addRow(self, startcolor="red"):
		currentCount = len(	self.fileChoosers )
		if (currentCount < 6):
			self.fileChoosers.append(FileChooserRow(self, row=currentCount + 1, column=0, columnspan=1, startcolor=startcolor))
		else:
			self.showErrorMessage("You cannot add any more files")

	"""Resize the root window to reflect current geometry"""
	def resizeFrame(self):
		self.winfo_toplevel().wm_geometry("") 

	def initialize(self):
		self.grid()
		
		self.fileChoosers = []
		self.addRow("red")
		self.addRow("green")
		self.addRow("blue")
		
		# these are row 20 to make sure that no rows are added below it
		self.addButton(20, 0, "Add Row", self.addRow)
		self.addButton(20, 1, "Process", self.processFiles)
		
		# set the focus on the entry field, cursor at the end
		self.fileChoosers[0].pathEntry.focus_set()
		self.fileChoosers[0].pathEntry.selection_range(0, Tkinter.END)
		
		# enable resizing of column 1
		#self.grid_columnconfigure(1,weight=1)
		
		
		# only resize horizontally
		self.resizable(True,False)  
		# fix Tk gui hiccup
		self.resizeFrame()	 



	################################################################################
	#
	# Callback commands
	#
	################################################################################
	def onButtonClick(self):
		valueToSet = self.getStringVariableValue(self.entryVariable) + " (You clicked the button)"
		self.setStringVariableValue(self.labelVariable, valueToSet)
	
	def onPressReturn(self, event):
		print "You pressed return!"
		
	def processFiles(self):
		filesAndColors = []
		for chooser in self.fileChoosers:
			filesAndColors.append( chooser.getFileAndColorAndFlags() ) #appends a tuple, (path, color, flags)
			print "Added a set with the color %s" % filesAndColors[-1][1]
			print "Flags: ", filesAndColors[-1][2]
		
		PNGDataSets = []
		
		if ( len(filesAndColors) == 0 ):
			print "No files to process"
			return
			
		full_path1 = os.path.abspath(filesAndColors[0][0])
		folder_path = os.path.split(full_path1)[0]
		dataset_folder = os.path.basename(folder_path)
		parent_directory = os.path.split(os.path.abspath(sys.argv[0]))[0]
		output_directory = os.path.join(parent_directory, "OutlierRemovedResults")
		if not os.path.exists(output_directory):
			os.makedirs(output_directory)
			print "Created directory %s" % output_directory
		else:
			print "Output directory %s exists" % output_directory
		
		for (file, color, flags) in filesAndColors:
			if (len(file) == 0):
				print "Still no files to process"
				return
			dataSet = ScienceFairProcess.getRawDataFromFile(file, color)
			if flags != None and flags.has_key("preprocess") and flags["preprocess"] == 1:
				print "Preprocess enabled for %s" % file
				# do preprocess here
				dataSet = ScienceFairProcess.zeroOutliersInDataSet(dataSet)
			PNGDataSets.append(dataSet)
		
		combinedSet = None
		for dataSet in PNGDataSets:
			if (combinedSet == None):
				combinedSet = dataSet
				print "New data set"
			else:
				combinedSet = ScienceFairProcess.combineTwoDataSets(combinedSet, dataSet)
				print "Added a data set"

		# now linear scale the combined
		x_axis_len = len(combinedSet)
		y_axis_len = len(combinedSet[0])
		
		#uncomment this to zero outliers
		#combinedSet = ScienceFairProcess.zeroOutliersInDataSet(combinedSet)
		
		# uncomment this to add linear scaling
		scaledSet = ScienceFairProcess.linearScaleDataSet(combinedSet)
		
		ScienceFairProcess.writePNGFile(scaledSet, output_directory, dataset_folder)
		ScienceFairProcess.histogramData(combinedSet, output_directory, dataset_folder)

		mean = ScienceFairProcess.getMean(scaledSet)
		means =  "The mean is %f" % mean
		
		median = ScienceFairProcess.getMedian(scaledSet)
		medians = "The median is %f" % median
		
		mode = ScienceFairProcess.getMode(scaledSet)
		modes = "The mode is %f" % mode
		
		pixel_max, pixel_min = ScienceFairProcess.getPixelRange(scaledSet, len(scaledSet), len(scaledSet[0]))
		ranges = "The range is %f" % (pixel_max - pixel_min)
		
		message = "Processing Complete! \r" + means + "\r" + medians + "\r" + modes + "\r" + ranges
		print message
		self.showInfoMessage(message)
		
if __name__ == "__main__":
	app = FITSImageProcessorApp(None)
	app.title("Ethan's FITS Image Processor")
	app.mainloop()
