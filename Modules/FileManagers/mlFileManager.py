import os, subprocess, pdb


class MLFileManager():
	def __init__(self, localMasterDir, cloudMasterDir):
		self.analysisDir = '__MachineLearningModels/'
		self.localMasterDir = localMasterDir + self.analysisDir
		self.cloudMasterDir = cloudMasterDir + self.analysisDir
		self._createFileDirectoryNames()
		self._downloadFile(self.videoModelFile)
		with open(self.localVideoModelFile) as f:
			line = next(f)
			line = next(f)
			self.vModelID = line.rstrip().split(',')[1]

	def downloadData(self):
		


		if os.path.exists(self.localMasterDir + '3D-Resnets'):
			commandOutput = subprocess.run(['git', 'pull', self.localMasterDir + '3D-Resnets', self.localMasterDir + '3D-Resnets'], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		else:
			commandOutput = subprocess.run(['git', 'clone', self.videoMLGithub, self.localMasterDir + '3D-Resnets'], stdout = subprocess.PIPE, stderr = subprocess.PIPE)

		self._downloadDirectory(self.vModelID)

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
		self.videoModelFile = 'MasterModels.txt'
		self.localVideoModelFile = self.localMasterDir + self.videoModelFile

		self.localVideoModelFile = self.localActiveDir + self.vModelID + '/model.pth'
		self.localVideoClassesFile = self.localActiveDir + self.vModelID + '/classInd.txt'
		self.localVideoCommandsFile = self.localActiveDir + self.vModelID + '/commands.pkl'
		self.localVideoPythonMainFile = self.localMasterDir + '3D-Resnets/main.py'
		self.localVideoPythonJsonFile = self.localMasterDir + '3D-Resnets/utils/cichlids_json.py'

	def _downloadFile(self, dfile):
		subprocess.call(['rclone', 'copy', self.cloudMasterDir + dfile, self.localMasterDir])
		if not os.path.exists(self.localMasterDir + dfile):
			raise FileNotFoundError('Unable to download ' + dfile + ' from ' + self.cloudMasterDir)

	def _downloadDirectory(self, directory):

		# First try to download tarred Directory
		subprocess.run(['rclone', 'copy', self.cloudMasterDir + directory, self.localMasterDir + directory])
		if not os.path.exists(self.localMasterDir + directory):
			raise FileNotFoundError('Unable to download ' + directory + ' from ' + self.cloudMasterDir)
