import os, subprocess, pdb


class MLFileManager():
	def __init__(self, localMasterDir, cloudMasterDir):
		self.analysisDir = '__MachineLearningModels/'
		self.localMasterDir = localMasterDir + self.analysisDir
		self.cloudMasterDir = cloudMasterDir + self.analysisDir
		self._createFileDirectoryNames()

	def _createFileDirectoryNames(self):
		self.videoModelsDir = 'VideoModels/'
		self.cloudVideoModelsDir = self.cloudMasterDir + self.videoModelsDir
		self.localVideoModelsDir = self.localMasterDir + self.videoModelsDir

		self.fishDetectionModelsDir = 'FishDetectionModels/'
		self.cloudFishDetectionModelsDir = self.cloudMasterDir + self.videoModelsDir
		self.localFishDetectionModelsDir = self.localMasterDir + self.videoModelsDir

		self.fishPoseModelsDir = 'DeepLabCutModels/'
		self.cloudVideoModelsDir = self.cloudMasterDir + self.videoModelsDir
		self.localVideoModelsDir = self.localMasterDir + self.videoModelsDir

		self.videoMLGithub = 'https://www.github.com/ptmcgrat/3D-Resnets'

	def prepareMLVideoClassification(self, vModelID):
		self.vModelID = vModelID

		self.cloudActiveDir = self.cloudVideoModelsDir
		self.localActiveDir = self.localVideoModelsDir

		if os.path.exists(self.localMasterDir + '3D-Resnets'):
			commandOutput = subprocess.run(['git', 'pull', self.localMasterDir + '3D-Resnets'], stdout = subprocess.PIPE, stdin = subprocess.PIPE)
		else:
			commandOutput = subprocess.run(['git', 'clone', self.videoMLGithub, self.localMasterDir + '3D-Resnets'], stdout = subprocess.PIPE, stdin = subprocess.PIPE)

		self._downloadDirectory(self.vModelID)
		self.localVideoModelFile = self.localActiveDir + vModelID + '/model.pth'
		self.localVideoClassesFile = self.localActiveDir + vModelID + '/classInd.txt'
		self.localVideoCommandsFile = self.localActiveDir + vModelID + '/commands.pkl'
		self.localVideoPythonMainFile = self.localMasterDir + '3D-Resnets/main.py'
		self.localVideoPythonJsonFile = self.localMasterDir + '3D-Resnets/utils/cichlids_json.py'


	def _downloadDirectory(self, directory):

		# First try to download tarred Directory
		subprocess.run(['rclone', 'copy', self.cloudActiveDir + directory, self.localActiveDir + directory])
		if not os.path.exists(self.localActiveDir + directory):
			raise FileNotFoundError('Unable to download ' + directory + ' from ' + self.cloudActiveDir)
