import datetime, os

from Modules.FileManagers.FileManager import FileManager as FM
from Modules.DataPreparers.PrepPreparer import PrepPreparer as PrP
from Modules.DataPreparers.DepthPreparer import DepthPreparer as DP
from Modules.DataPreparers.ClusterPreparer import ClusterPreparer as CP
from Modules.DataPreparers.MLClusterPreparer import MLClusterPreparer as MLP

class ProjectPreparer():
	# This class takes in a projectID and runs all the appropriate analysis

	def __init__(self, projectID, workers = None):

		self.projectID = projectID
		self.workers = workers
		self.fileManager = FM()
		self.projFileManager = self.fileManager.retProjFileManager(projectID) 
		self.mlFileManager = self.fileManager.retMLFileManager(projectID) 

	def downloadData(self, dtype):
		self.fileManager.createDirs()
		self.projFileManager.downloadData(dtype)
		if dtype in ['Download', 'MLClassification']:
			self.mlFileManager.downloadData()

	def runPrepAnalysis(self):
		prp_obj = PrP(self.projFileManager)
		prp_obj.validateInputData()
		prp_obj.prepData()
		self.createUploadFile(prp_obj.uploads)
		self.createAnalysisUpdate('Prep', prp_obj)

	def runDepthAnalysis(self):
		dp_obj = DP(self.projFileManager, self.workers)
		dp_obj.validateInputData()
		dp_obj.createSmoothedArray()
		dp_obj.createRGBVideo()
		self.createUploadFile(dp_obj.uploads)
		self.createAnalysisUpdate('Depth', dp_obj)

	def runClusterAnalysis(self):
		avp_obj = AVP(self.projFileManager)
		avp_obj.validateInputData()
		avp_obj.runClusterAnalysis()
		self.createUploadFile(avp_obj.uploads)
		self.createAnalysisUpdate('Cluster', avp_obj)

	def runMLClusterClassifier(self):
		mlc_obj = MLC(self.projFileManager, self.mlFileManager)
		mlc_obj.validateInputData()
		mlc_obj.predictVideoLabels()
		self.createUploadFile(mlc_obj.uploads)
		self.createAnalysisUpdate('MLClassifier', mlc_obj)

	def runMLFishDetection(self):
		pass

	def backupAnalysis(self):
		uploadCommands = set()

		uploadFiles = [x for x in os.listdir(self.fileManager.localUploadDir) if 'UploadData' in x]

		for file in uploadFiles:
			with open(uFile) as f:
				line = next(f)
				for line in f:
					tokens = line.split(',')
					tokens[2] = bool(tokens[2])
					uploadCommands.add(tuple(tokens))

		for command in uploadCommands:
			self.fileManager.uploadData(tokens[0],tokens[1], tokens[2])

		self.fileManager.uploadData(self.fileManager.localAnalysisUpdateDir, self.fileManager.cloudAnalysisUpdateDir, False)


	def createUploadFile(self, uploads):
		with open(self.fileManager.localUploadDir + 'UploadData_' + str(now) + '.csv', 'w') as f:
			print('Local,Cloud,Tar', file = f)
			for upload in uploads:
				print(upload[0] + ',' + upload[1] + ',' + upload[2], file = f)

	def createAnalysisUpdate(self, aType, procObj):
		now = datetime.datetime.now()
		with open(self.fileManager.localAnalysisUpdateDir + 'AnalysisUpdate_' + str(now) + '.csv', 'w') as f:
			print('ProjectID,Type,Version,Date', file = f)
			print(self.projectID + ',' + aType + ',' + procObj.__version__ + ',' + os.getenv('USER') + '_' + str(now), file= f)
