import subprocess, os

class AnFileManager():
	def __init__(self, localMasterDir, cloudMasterDir):
		self.analysisDir = '__AnalysisLog/'
		self.localMasterDir = localMasterDir + self.analysisDir
		self.cloudMasterDir = cloudMasterDir + self.analysisDir

		self.analysisSummaryFile = 'AnalyzedProjects.xlsx'
		self.localAnalysisSummaryFile = self.localMasterDir + self.analysisSummaryFile
		self._createDirectory(self.localMasterDir)

	def downloadAnalysisDir(self):
		self._downloadDirectory('')

	def backupAnalysisDir(self):
		self._uploadDirectory('')

	def deleteAnalysisDir(self):
		subprocess.run(['rm', '-rf', self.localMasterDir])

	def uploadAnalysisUpdate(self, updateFile):
		self._uploadFile(updateFile)

	def _createDirectory(self, directory):
		if not os.path.exists(directory):
			os.makedirs(directory)

	def _downloadFile(self, dfile):
		subprocess.call(['rclone', 'copy', self.cloudMasterDir + dfile, self.localMasterDir], stderr = subprocess.PIPE)
		if not os.path.exists(self.localMasterDir + dfile):
			raise FileNotFoundError('Unable to download ' + dfile + ' from ' + self.cloudMasterDir)

	def _downloadDirectory(self, directory):

		# First try to download tarred Directory
		tar_directory = directory[:-1] + '.tar'
		subprocess.run(['rclone', 'copy', self.cloudMasterDir + tar_directory, self.localMasterDir], stderr = subprocess.PIPE)
		if os.path.exists(self.localMasterDir + tar_directory):
			print(['tar', '-xvf', self.localMasterDir + tar_directory, '-C', self.localMasterDir])
			subprocess.run(['tar', '-xvf', self.localMasterDir + tar_directory, '-C', self.localMasterDir], stderr = subprocess.PIPE)
			if not os.path.exists(self.localMasterDir + directory):
				raise FileNotFoundError('Unable to untar ' + tar_directory)
			else:
				subprocess.run(['rm', '-f', self.localMasterDir + tar_directory])

		else:
			out = subprocess.run(['rclone', 'copy', self.cloudMasterDir + directory, self.localMasterDir + directory], stderr = subprocess.PIPE)
			if not os.path.exists(self.localMasterDir + directory):
				print(['rclone', 'copy', self.cloudMasterDir + directory, self.localMasterDir + directory])
				raise FileNotFoundError('Unable to download ' + directory + ' from ' + self.cloudMasterDir + ' ' + out.stderr.decode())

	def _uploadDirectory(self, directory, tar = False):
		if tar:
			if directory[-1] == '/':
				directory = directory[:-1]

			subprocess.run(['tar', '-cvf', self.localMasterDir + directory + '.tar', '-C', self.localMasterDir, directory], stderr = subprocess.PIPE)
			command = ['rclone', 'copy', self.localMasterDir + directory, self.cloudMasterDir]
		else:
			command = ['rclone', 'copy', self.localMasterDir + directory, self.cloudMasterDir + directory]
	
		output = subprocess.run(command, stdout = subprocess.PIPE, stderr = subprocess.PIPE, encoding = 'utf-8')
		if output.stderr != '':
			print(command)
			print(output.stderr)
			pdb.set_trace()
			raise Exception('rclone was not able to sync ' + directory)

	def _uploadFile(self, dfile):
		subprocess.call(['rclone', 'copy', self.localMasterDir + dfile, self.cloudMasterDir], stderr = subprocess.PIPE)
		if not os.path.exists(self.localMasterDir + dfile):
			raise FileNotFoundError('Unable to upload ' + dfile + ' from ' + self.localMasterDir)


