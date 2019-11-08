import datetime

from Modules.LogParser import LogParser as LP
from Modules.FileManager import FileManager as FM
from Modules.DataPreparers.VideoPreparer import VideoPreparer as VP

class AllVideosPreparer():
	# This class takes in directory information and a logfile containing depth information and performs the following:
	# 1. Identifies tray using manual input
	# 2. Interpolates and smooths depth data
	# 3. Automatically identifies bower location
	# 4. Analyze building, shape, and other pertinent info of the bower

	def __init__(self, projectID, workers = 24):

		self.projectID = projectID
		self.workers = 24
		self.fileManager = FM()
		self.anFileManager = self.fileManager.retAnFileManager()
		self.projFileManager = self.fileManager.retProjFileManager(projectID)
		self.mlFileManager = self.fileManager.retMLFileManager()

	def __del__(self):
		pass
		#self.projFileManager.localDelete()

	def seriesClusterAnalysis(self, workers):
		self.prepareAllClusterData()
		self.runClusterAnalysis(parallel = False, workers = workers)
		self.createClusterAnalysisUpdate()
		self.backupClusterData()


	def prepareAllClusterData(self):
		print('Downloading data necessary for cluster analysis of ' + self.projectID + ',,Time: ' + str(datetime.datetime.now()))

		self.projFileManager.prepareClusterAnalysis()
		self.lp = LP(self.projFileManager.localLogfile)


	def prepareAllMLData(self, mlModelID):
		print('Downloading data necessary for ML analysis of ' + self.projectID + ',,Time: ' + str(datetime.datetime.now()))

		self.projFileManager.prepareMLVideoAnalysis()
		self.mlFileManager.prepareMLVideoClassification(mlModelID)
		self.lp = LP(self.projFileManager.localLogfile)


	def backupClusterData(self):
		self.projFileManager.backupClusterAnalysis()
		self.projFileManager.localDelete()
		self.anFileManager.deleteAnalysisDir()

	def runClusterAnalysis(self, parallel = False):
		clusterData = []
		self.vp_objs = []
		for index in range(len(self.lp.movies)):
			print('Processing video: ' + self.lp.movies[index].mp4_file + ',,Time: ' + str(datetime.datetime.now()))
			self.vp_objs.append(VP(self.projFileManager, index, self.workers))
			if not parallel:				
				clusterData.append(self.vp_objs[index].processVideo())
		if parallel:
			from multiprocessing.dummy import Pool as ThreadPool
			pool = ThreadPool(workers)
			clusterData = pool.map(self.parallelVideoProcesser, list(range(len(self.lp.movies))))
		allClusterData = pd.concat(clusterData)
		allClusterData.to_csv(self.projFileManager.localAllLabeledClustersFile, sep = ',')

	def parallelVideoProcesser(self, index):
		return(self.vp_objs[index].processVideo())

	def predictClusterLabels(self, vModelID):
		self.projFileManager.prepareMachineLearningAnalysis()
		self.mlFileManager.prepareMLVideoClassification(self, vModelID)
		ml_obj = MLP(self.projFileManager)
		ml_obj.predictVideoLabels(self.mlFileManager)
		self.projFileManager.backupMachineLearningAnalysis()

	def createClusterAnalysisUpdate(self):
		now = datetime.datetime.now()
		with open(self.anFileManager.localMasterDir + 'AnalysisUpdate_' + str(now) + '.csv', 'w') as f:
			print('ProjectID,Type,Version,Date', file = f)
			print(self.projectID + ',Video,' + os.getenv('USER') + '_' + self.vp_objs[0].__version__ + ',' + str(now), file= f)
		self.anFileManager.uploadAnalysisUpdate('AnalysisUpdate_' + str(now) + '.csv')

	def createMachineLearningAnalysisUpdate(self):
		now = datetime.datetime.now()
		with open(self.anFileManager.localMasterDir + 'AnalysisUpdate_' + str(now) + '.csv', 'w') as f:
			print('ProjectID,Type,Version,Date', file = f)
			print(self.projectID + ',Video,' + os.getenv('USER') + '_' + self.vp_objs[0].__version__ + ',' + str(now), file= f)
		self.anFileManager.uploadAnalysisUpdate('AnalysisUpdate_' + str(now) + '.csv')