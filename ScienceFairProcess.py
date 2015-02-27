#!/usr/bin/env python
"""
Written by Ethan Shaw
"""
from astropy.io import fits
import sys, png, math, os

colors = ['red', 'green', 'blue']

# Build x_axis_len rows, each containing y_axis_len columns
# access with PNG_data[row][column]
def buildMatrix(x_axis_len, y_axis_len, greyscale=True):
	# set up empty list (matrix) to hold pixels
	PNG_data = []
	for row in range(0, x_axis_len):
	   PNG_data.append([])
	   #start out with an empty list, then put another list in it so it looks like [[]]
	   #gives the value of x_axis_len empty lists inside the list PNG_data
	   for column in range (0, y_axis_len):
		  if ( greyscale ):
			 PNG_data[row].append(0)
			 #this is the grayscale value
		  else:
		  	#Red,Green,Blue values
			 PNG_data[row].append(0)
			 PNG_data[row].append(0)
			 PNG_data[row].append(0)
	return PNG_data

#Function defines ONLY color
def setPixel(PNG_data, red, green, blue, row, column):
	PNG_data[row][column*3] = red
	PNG_data[row][column*3 + 1] = green
	PNG_data[row][column*3 + 2] = blue

def getPixelRange(PNG_data, x_axis_len, y_axis_len):
	# determine the PNG_data range for scaling purposes
	pixel_max = 0
	pixel_min = pow(2,16)
	for row in range(0, x_axis_len):
		for column in range (0, y_axis_len):
			pixel_max = max(pixel_max, PNG_data[row][column])
			pixel_min = min(pixel_min, PNG_data[row][column])
	
	print "Pixel max: {0:.20f}, Pixel min: {0:.20f}".format(pixel_max, pixel_min)
	return (pixel_max, pixel_min)

def getRawDataFromFile(file, color):
	#this reads the file and structures into useable format
	hdulist = fits.open(file)
	entry = hdulist[0]
	
	bits_per_pixel = entry.header['BITPIX']
	number_axis = entry.header['NAXIS']
	x_axis_len = entry.header['NAXIS2']
	y_axis_len = entry.header['NAXIS1']
	print "Data dimensions: (%d x %d) - %d axes, %d bpp" % (x_axis_len, y_axis_len, number_axis, bits_per_pixel)

	# data is a bunch of columns, each containing one row
	data = entry.data
	
	pixelData = buildMatrix(x_axis_len, y_axis_len, greyscale=False)
	for row in range(0, x_axis_len):
		for column in range (0, y_axis_len):
				 try:				 
					 image_value = data[row][column]
					 red, green, blue = ( 0,0,0 )
					 if ( color == 'red' ):
						 red = image_value
					 elif ( color == 'green' ):
						 green = image_value
					 elif ( color == 'blue' ):
						 blue = image_value

					 setPixel(pixelData, red, green, blue, row, column)
					 
				 except Exception as e:
					 print "Error accessing (%d, %d) : %s" % (row, column, e)
					 raise SystemExit
	
	return pixelData

def combineTwoDataSets(dataSet1, dataSet2):
	print "Combining two data sets"
	# step 1, make a new data set the size of the two
	x_axis_len = len(dataSet1)
	y_axis_len = len(dataSet1[0])
	combinedData = buildMatrix(x_axis_len, y_axis_len)
	# step 2, step over each pixel in the sets and ADD to the combined pixel value
	for row in range(0, x_axis_len):
		for column in range (0, y_axis_len):
			combinedData[row][column] = dataSet1[row][column] + dataSet2[row][column]
	# step 3, return the combined data set
	return combinedData

def writePNGFile(PNGData, output_directory, dataset_name):
	filename = '%s/out_data_%s.png' % ( output_directory, dataset_name)
	f = open(filename, 'wb')	  # binary mode is important
	w = png.Writer(len(PNGData[0])/3, len(PNGData), greyscale=False,alpha=False, bitdepth=16)
	w.write(f, PNGData)
	print "Image written to file %s" % filename

def linearScale(value, min_value, max_value):
	pixel_range = abs(max_value - min_value)
	#2 to the 16th means a 16 bit image (using 16 bits of data to describe each pixel)
	ratio = (pow(2, 16)*1.0 - 1) / pixel_range
	#This gives us a linearly scaled value between 0 (black) and 2^16 (white)
	val = int(round(value * ratio))
	return val

def logarithmicScalePixel(value, min_value, max_value):
	try:
		val = abs(math.log(value))
		# for min and max we use 0, 100 for now
		return linearScalePixel(val, 0, 100)
	except Exception as e:
		return 0 

def linearScalePixel(value, min_value, max_value):

	pixel_range = abs(max_value - min_value)
	#2 to the 16th means a 16 bit image (using 16 bits of data to describe each pixel)
	ratio = (pow(2, 16)*1.0 -1 ) / pixel_range
	
	#This gives us a linearly scaled value between 0 (black) and 2^16 (white)
	val = int(round(value * ratio))
	
	if ( val < 0 or val > 65535 ):
		print "value %d (orig: %f was outside range %.e, %.e" % ( val, value, min_value, max_value )
		raise SystemExit
	
	return val

def scaleDataSet(scalingFunction, dataSet):
	x_axis_len = len(dataSet)
	y_axis_len = len(dataSet[0])
	pixel_max, pixel_min = getPixelRange(dataSet, x_axis_len, y_axis_len)
	
	print "Max: %f, Min: %f" % (pixel_max, pixel_min)

	for row in range(0, x_axis_len):
		for column in range (0, y_axis_len):
				dataSet[row][column] = scalingFunction(dataSet[row][column], pixel_min, pixel_max)
	return dataSet

def linearScaleDataSet(dataSet):
	return scaleDataSet(linearScalePixel, dataSet)

def logScaleDataSet(dataSet):
	return scaleDataSet(logarithmicScalePixel, dataSet)

def zeroOutliersInDataSet(dataSet, interQuartileScaleFactor=1.5):
	(firstQuartile, median, thirdQuartile, interQuartile) = getQuartileValues(dataSet)
	minAllowedValue = max(0, firstQuartile - (interQuartileScaleFactor * interQuartile))
	maxAllowedValue = thirdQuartile + (interQuartileScaleFactor * interQuartile)
	
	x_axis_len = len(dataSet)
	y_axis_len = len(dataSet[0])
	for row in range(0, x_axis_len):
		for column in range (0, y_axis_len):
			dataValue = dataSet[row][column]
			if (dataValue < minAllowedValue or dataValue > maxAllowedValue):
				dataSet[row][column] = 0
	return dataSet

def histogramData(dataSet, output_directory, dataset_folder="data"):
	pixel_max, pixel_min = getPixelRange(dataSet, len(dataSet), len(dataSet[0]))
	
	histogram = {}
	
	number_of_groups = 10
	group_size = (pixel_max - pixel_min) / (number_of_groups *1.0)
	
	for i in range(0, number_of_groups):
		histogram[int(i*group_size)] = 0

	histogramKeys = histogram.keys()
	histogramKeys.sort()
	histogramKeys.reverse()
	
	for x in range(0, len(dataSet)):
		for y in range(0, len(dataSet[0])):
			pixel = dataSet[x][y]
			for key in histogramKeys:
				if pixel < key:
					histogram[key] = int(histogram[key] + 1)
					continue

	histogramKeys.reverse()
	output_path = "%s/%s_histogram.csv" % (output_directory, dataset_folder)
	outf = open(output_path, "w")
	for key in histogramKeys:
		kname = "Bucket %d"  % key
		outf.write("%s,%d\n" % (kname, histogram[key]))
	outf.close()
	print "Histogram written to file %s" % output_path

def getMean(dataSet):
	sum = 0.0
	count = 0
	x_axis_len = len(dataSet)
	y_axis_len = len(dataSet[0])
	for row in range(0, x_axis_len):
		for column in range (0, y_axis_len):
			if dataSet[row][column] > 0:
				sum = sum + dataSet[row][column]
				count = count + 1
	return sum/count

def getMedian(dataSet):
	dataList = []
	x_axis_len = len(dataSet)
	y_axis_len = len(dataSet[0])
	for row in range(0, x_axis_len):
		for column in range (0, y_axis_len):
			if (dataSet[row][column] > 0):
				dataList.append(dataSet[row][column])
	dataList.sort()
	middleNumber = len(dataList)/2
	return dataList[middleNumber]

def getQuartileValues(dataSet):
	median = getMedian(dataSet)
	x_axis_len = len(dataSet)
	y_axis_len = len(dataSet[0])
	
	valuesLessThanMedian = []
	valuesGreaterThanMedian = []
	
	for row in range(0, x_axis_len):
		for column in range (0, y_axis_len):
			if dataSet[row][column] > median:
				valuesGreaterThanMedian.append(dataSet[row][column])
			else:
				valuesLessThanMedian.append(dataSet[row][column])
	valuesGreaterThanMedian.sort()
	valuesLessThanMedian.sort()
	firstQuartile = valuesLessThanMedian[len(valuesLessThanMedian)/2]
	thirdQuartile = valuesGreaterThanMedian[len(valuesGreaterThanMedian)/2]
	
	interQuartile = thirdQuartile - firstQuartile
	
	print "Quartiles: ", firstQuartile, median, thirdQuartile, interQuartile
	
	return (firstQuartile, median, thirdQuartile, interQuartile)

def getMode(dataSet):
	dataPoints = {}
	x_axis_len = len(dataSet)
	y_axis_len = len(dataSet[0])
	for row in range(0, x_axis_len):
		for column in range (0, y_axis_len):
			point = dataSet[row][column]
			if (point > 0):
				if dataPoints.has_key(point):
					dataPoints[point] =  dataPoints[point] + 1
				else:
					dataPoints[point] = 1
	
	maxCount = 0
	maxValue = None
	
	for (value, count) in dataPoints.items():
		if count > maxCount:
			maxCount = count
			maxValue = value
	
	print "%f was the max value and occurred %d times" % (maxValue, maxCount)
	return maxValue
	
def outputToCSVFile(filename, dataSet):
	outf = open(filename, 'w')
	
	x_axis_len = len(dataSet)
	y_axis_len = len(dataSet[0])
	
	for row in range(0, x_axis_len):
		line = ""
		for column in range (0, y_axis_len):
			line = "%s%.7e," % (line, dataSet[row][column])
		line = line + "\n"
		outf.write(line)
	outf.close()
	print "Wrote to %s" % filename

if __name__ ==  "__main__":
	if len(sys.argv) < 2:
		print "Usage: %s <file1> <file2> ..." % sys.argv[0]
		raise SystemExit		
	files = sys.argv[1:]
	i = 0
	PNGDataSets = []
	
	#rData = getRawDataFromFile(files[0], "red")
	#writePNGFile(rData, "red")
	#raise SystemExit
	
	full_path1 = os.path.abspath(files[0])
	folder_path = os.path.split(full_path1)[0]
	dataset_folder = os.path.basename(folder_path)
	
	for file in files:
		dataSet = getRawDataFromFile(file, colors[i])
		i = i + 1
		dataSetNormalized = zeroOutliersInDataSet(dataSet)
		PNGDataSets.append(dataSetNormalized)
	
	combinedSet = None
	for dataSet in PNGDataSets:
		if (combinedSet == None):
			combinedSet = dataSet
		else:
			combinedSet = combineTwoDataSets(combinedSet, dataSet)

	parent_directory = os.path.split(os.path.abspath(sys.argv[0]))[0]
	output_directory = os.path.join(parent_directory, "Results")
	if not os.path.exists(output_directory):
		os.makedirs(output_directory)
		print "Created directory %s" % output_directory
	else:
		print "Output directory %s exists" % output_directory

	# now linear scale the outlier set
	scaledSet = linearScaleDataSet(combinedSet)
	histogramData(scaledSet, output_directory, dataset_folder)
		
	#raise SystemExit

	filename = "%s/dataset_%s.csv" % (output_directory, dataset_folder)
	outputToCSVFile(filename, scaledSet)
	writePNGFile(scaledSet, output_directory, dataset_folder) #old was writePNGFile(combinedSet, "combined")
	
	print "Process complete"