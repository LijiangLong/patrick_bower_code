import scipy.signal
import numpy as np
import cv2, pdb, os
from Modules.DataObjects.LogParser import LogParser as LP

class DepthPreparer:
	# This class takes in directory information and a logfile containing depth information and performs the following:
	# 1. Identifies tray using manual input
	# 2. Interpolates and smooths depth data
	# 3. Automatically identifies bower location
	# 4. Analyze building, shape, and other pertinent info of the bower

	def __init__(self, projFileManager, workers):
		
		self.__version__ = '1.0.0'
		self.projFileManager = projFileManager

	def validateInputData(self):
		assert os.path.exists(self.projFileManager.localLogfile)
		self.lp = LP(self.projFileManager.localLogfile)

		for frame in self.lp.frames:
			assert os.path.exists(self.projFileManager.localMasterDir + frame.npy_file)
			assert os.path.exists(self.projFileManager.localMasterDir + frame.pic_file)
		assert os.path.exists(self.projFileManager.localTroubleshootingDir)
		assert os.path.exists(self.projFileManager.localAnalysisDir)

		self.uploads = [(self.projFileManager.localTroubleshootingDir, self.projFileManager.cloudTroubleshootingDir, '0'), 
						(self.projFileManager.localAnalysisDir, self.projFileManager.cloudAnalysisDir, '0')]


	def createSmoothedArray(self, totalGoodData = 0.3, minGoodData = 0.5, minUnits = 5, tunits = 71, order = 4):
		# Download raw data and create new array to store it
		rawDepthData = np.empty(shape = (len(self.lp.frames), self.lp.height, self.lp.width))
		for i, frame in enumerate(self.lp.frames):                
			try:
				data = np.load(self.projFileManager.localMasterDir + frame.npy_file)
			except ValueError:
				self._print('Bad frame: ' + str(i) + ', ' + frame.npy_file)
				rawDepthData[i] = self.rawDepthData[i-1]
			else:
				rawDepthData[i] = data

		# Convert to cm
		rawDepthData = 100/(-0.0037*rawDepthData + 3.33)
		rawDepthData[(rawDepthData < 40) | (rawDepthData > 80)] = np.nan # Values that are too close or too far are set to np.nan

		np.save(self.projFileManager.localRawDepthFile, rawDepthData)

		# Make copy of raw data
		interpDepthData = rawDepthData.copy()

		# Count number of good pixels
		goodDataAll = np.count_nonzero(~np.isnan(interpDepthData), axis = 0) # number of good data points per pixel
		goodDataStart = np.count_nonzero(~np.isnan(interpDepthData[:100]), axis = 0) # number of good data points in the first 5 hours

		numFrames = len(self.lp.frames)
		nans = np.cumsum(np.isnan(interpDepthData), axis = 0)
		
		# Process each pixel
		for i in range(rawDepthData.shape[1]):
			for j in range(rawDepthData.shape[2]):
				if goodDataAll[i,j] > totalGoodData*numFrames or goodDataStart[i,j] > minGoodData*100:
					bad_indices = np.where(nans[minUnits:,i,j] - nans[:-1*minUnits,i,j] == minUnits -1)[0] + int(minUnits/2)+1
					interpDepthData[bad_indices,i,j] = np.nan

					nan_ind = np.isnan(interpDepthData[:,i,j])
					x_interp = np.where(nan_ind)[0]
					x_good = np.where(~nan_ind)[0]

					l_data = interpDepthData[x_good[:10], i, j].mean()
					r_data = interpDepthData[x_good[-10:], i, j].mean()

					try:
						interpDepthData[x_interp, i, j] = np.interp(x_interp, x_good, interpDepthData[x_good, i, j], left = l_data, right = r_data)
					except ValueError:
						self._print(str(x_interp) + ' ' + str(x_good))
				else:
					interpDepthData[:,i,j] = np.nan
						
		np.save(self.projFileManager.localInterpDepthFile, interpDepthData)
		smoothDepthData = scipy.signal.savgol_filter(interpDepthData, tunits, order, axis = 0, mode = 'mirror')
		np.save(self.projFileManager.localSmoothDepthFile, smoothDepthData)

	def createRGBVideo(self):
		self.lp = LP(self.projFileManager.localLogfile)
		for i, frame in enumerate(self.lp.frames): 
			depthRGB = cv2.imread(self.projFileManager.localMasterDir + frame.pic_file)
			if i==0:
				#pdb.set_trace()
				outMovie = cv2.VideoWriter(self.projFileManager.localRGBDepthVideo, cv2.VideoWriter_fourcc(*"mp4v"), 30.0, (depthRGB.shape[1],depthRGB.shape[0]))
			outMovie.write(depthRGB)

		outMovie.release()



