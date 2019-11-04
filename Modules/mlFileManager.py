import os, subprocess, pdb


class MLFileManager():
	def __init__(self):
		self.rcloneRemote = 'cichlidVideo'
		self.videoMLGithub = 'https://github.com/ptmcgrat/3D-Resnets'

		self.cloudMasterDir = self.rcloneRemote + ':McGrath/Apps/CichlidPiData/__MachineLearningModels/'
		self.localMasterDir = os.getenv('HOME') + '/' + 'Temp/CichlidAnalyzer/__MachineLearningModels/'

	def _createFileDirectoryNames(self):
		self.videoModelsDir = 'VideoModels/'
		self.cloudVideoModelsDir = self.cloudMasterDir + self.videoModelsDir
		self.localVideoModelsDir = self.localMasterDir + self.videoModelsDir

		self.fishDetectionModelsDir = 'FishDetectionModels/'
		self.cloudFishDetectionModelsDir = self.cloudMasterDir + self.videoModelsDir
		self.localFishDetectionModelsDir = self.localMasterDir + self.videoModelsDir

		self.fishPoseModelsDir = 'FishPoseModels/'
		self.cloudVideoModelsDir = self.cloudMasterDir + self.videoModelsDir
		self.localVideoModelsDir = self.localMasterDir + self.videoModelsDir

	def prepareMLVideoClassification(self, vModelID):
		self.vModelID = vModelID

		self.cloudActiveDir = self.cloudVideoModelsDir
		self.localActiveDir = self.localVideoModelsDir

		subprocess.run(['git', 'clone', self.videoMLGithub])

		self._downloadDirectory(self.vModelID)
		self.localVideoModelFile = self.localActivDir + vModelID + '/model.pth'
		self.localVideoClassesFile = self.localActivDir + vModelID + '/classInd.txt'
		self.localVideoCommandsFile = self.localActivDir + vModelID + '/commands.pkl'
		self.localVideoPythonFile = '3D-Resnets/main.py'

	def _downloadDirectory(self, directory):

		# First try to download tarred Directory
		subprocess.run(['rclone', 'copy', self.cloudActive + directory, self.localActiveDir + directory], stderr = self.errorLog)
		if not os.path.exists(self.localActiveDir + directory):
			raise FileNotFoundError('Unable to download ' + directory + ' from ' + self.cloudMasterDir)
