from Modules.FileManager import FileManager as FM
from Modules.DataPreparers.CropPreparer import CropPreparer as CP
from Modules.DataPreparers.DepthPreparer import DepthPreparer as DP
from Modules.DataPreparers.VideoPreparer import VideoPreparer as VA

import pandas as pd

class DataAnalyzer:
	# This class takes in directory information and a logfile containing depth information and performs the following:
	# 1. Identifies tray using manual input
	# 2. Interpolates and smooths depth data
	# 3. Automatically identifies bower location
	# 4. Analyze building, shape, and other pertinent info of the bower

	def __init__(self, fileManager):
		self.fileManager = fileManager

	def __del__(self):
		self.fileManager.localDelete()

	def preparePrep(self):
		self.fileManager.prepareCropAnalysis()
		cp_obj = CP(self.fileManager)
		cp_obj.prepData()
		self.fileManager.backupCropAnalysis()

	def prepareDepth(self):
		self.fileManager.prepareDepthAnalysis()
		dpt_obj = DP(self.fileManager)
		dpt_obj.createSmoothedArray()
		self.fileManager.backupDepthAnalysis()

	def prepareVideos(self):
		self.fileManager.prepareVideoAnalysis()

		clusterData = []
		for index in range(len(self.fileManager.movies))
			vp_obj = VA(fm_obj, 0, 8)
			clusterData.append(vp_obj.processVideo())

		allClusterData = pd.concat(pdList)
		allClusterData.to_csv(self.fileManager.localAllLabeledClustersFile, sep = ',')

		self.fileManager.backupVideoAnalysis()
