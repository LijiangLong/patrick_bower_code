from Modules.ProjFileManager import ProjFileManager as ProjFM
from Modules.mlFileManager import MLFileManager as ML_FM
from Modules.DataPreparers.CropPreparer import CropPreparer as CP
from Modules.DataPreparers.DepthPreparer import DepthPreparer as DP
from Modules.DataPreparers.VideoPreparer import VideoPreparer as VP
from Modules.DataPreparers.MachineLearningPreparer import MachineLearningPreparer as MLP
from Modules.LogParser import LogParser as LP

import pandas as pd

class DataPreparer:
	# This class takes in directory information and a logfile containing depth information and performs the following:
	# 1. Identifies tray using manual input
	# 2. Interpolates and smooths depth data
	# 3. Automatically identifies bower location
	# 4. Analyze building, shape, and other pertinent info of the bower

	def __init__(self, projectID):
		self.projectID = projectID
		self.projFileManager = ProjFM(projectID)
		self.mlFileManager = ML_FM()

	def __del__(self):
		pass
		#self.projFileManager.localDelete()

	def preparePrep(self):
		self.projFileManager.prepareCropAnalysis()
		cp_obj = CP(self.projFileManager)
		cp_obj.prepData()
		self.projFileManager.backupCropAnalysis()

	def prepareDepth(self):
		self.projFileManager.prepareDepthAnalysis()
		dpt_obj = DP(self.projFileManager)
		dpt_obj.createSmoothedArray()
		self.projFileManager.backupDepthAnalysis()

	def prepareVideos(self):
		"""self.projFileManager.prepareVideoAnalysis()
		self.lp = LP(self.projFileManager.localLogfile)

		clusterData = []
		for index in range(len(self.lp.movies)):
			vp_obj = VP(self.projFileManager, index, 8)
			clusterData.append(vp_obj.processVideo())
			break

		allClusterData = pd.concat(clusterData)
		allClusterData.to_csv(self.projFileManager.localAllLabeledClustersFile, sep = ',')
		"""
		self.projFileManager.backupVideoAnalysis()

	def predictClusterLabels(self, vModelID):
		self.projFileManager.prepareMachineLearningAnalysis()
		self.mlFileManager.prepareMLVideoClassification(self, vModelID)
		ml_obj = MLP(self.projFileManager)
		ml_obj.predictVideoLabels(self.mlFileManager)
		self.projFileManager.backupMachineLearningAnalysis()



