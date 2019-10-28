import os, subprocess, pdb


class FileManager():
	def __init__(self, projectID, localMasterDir = None):
		self.projectID = projectID
		self.system = 'computer' # Initially assume  that we are on a laptop/desktop/server

		self.rcloneRemote = 'cichlidVideo'
		self.cloudMasterDir = self.rcloneRemote + ':McGrath/Apps/CichlidPiData/' + self.projectID + '/'

		if localMasterDir is None:
			self.localMasterDir = os.getenv('HOME') + '/' + 'Temp/CichlidAnalyzer/' + self.projectID + '/'
			self._identifyPiDirectory() # Determine if we are on a raspberry pi and if so identify directory
		else:
			self.localMasterDir = localMasterDir


		self._createDirectory(self.localMasterDir)

		self._createFileDirectoryNames()		
		self._createParameters()

		self.errorLog = open(self.localMasterDir + 'ErrorLog.txt', 'a')

	def prepareCropAnalysis(self):
		self._createDirectory(self.localMasterDir)
		self._createDirectory(self.localAnalysisDir)
		self._createDirectory(self.localFigureDir)
		self._downloadFile(self.logfile)
		self._downloadDirectory(self.prepDir)

	def backupCropAnalysis(self):
		self._uploadDirectory(self.analysisDir)
		self._uploadDirectory(self.figureDir)

	def prepareDepthAnalysis(self):
		self._createDirectory(self.localMasterDir)
		self._createDirectory(self.localAnalysisDir)
		self._createDirectory(self.localTroubleshootingDir)
		self._downloadFile(self.logfile)
		self._downloadDirectory(self.frameDir)

	def backupDepthAnalysis(self):

		self._uploadDirectory(self.analysisDir)
		self._uploadDirectory(self.troubleshootingDir)

	def prepareVideoAnalysis(self, index):
		self._createDirectory(self.localMasterDir)
		self._createDirectory(self.localAnalysisDir)
		self._createDirectory(self.localTroubleshootingDir)
		self._createDirectory(self.localFigureDir)

		self._downloadFile(self.logfile)
		self._downloadDirectory(self.videoDir)
		self.lp = LP(self.localLogFile)
		for vo in self.lp.movies:
			vo.localAnalysisDir = self.localAnalysisDir + vo.baseName + '/'
			vo.localTroubleshootingDir = self.localAnalysisDir + vo.baseName + '/'

			self._createDirectory(vo.localAnalysisDir)
			self._createDirectory(vo.localTroubleshootingDir)

	def prepareFigureAnalysis(self):
		self._createDirectory(self.localMasterDir)
		self._createDirectory(self.localFigureDir)
		self._downloadFile(self.logfile)
		self._downloadDirectory(self.analysisDir)

	def backupFigureAnalysis(self):

		self._uploadDirectory(self.figureDir)

	def localDelete(self):
		subprocess.run(['rm','-rf', self.localMasterDir])


	def _createFileDirectoryNames(self):
		# Create logfile
		self.logfile = 'Logfile.txt'
		self.localLogfile = self.localMasterDir + self.logfile

		# Data directories created by tracker
		self.prepDir = 'PrepFiles/'
		self.frameDir = 'Frames/'
		self.backgroundDir = 'Backgrounds/'
		self.videoDir = 'Videos/'

		# Directories created by analysis scripts
		self.analysisDir = 'MasterAnalysisFiles/'
		self.localAnalysisDir = self.localMasterDir + 'MasterAnalysisFiles/'
		self.figureDir = 'Figures/'
		self.localFigureDir = self.localMasterDir + 'Figures/'
		self.labelClipAnalysis = 'LabelClips/'
		self.mlClipAnalysis = 'MLClips/'
		self.troubleshootingDir = 'Troubleshooting/'
		self.localTroubleshootingDir = self.localMasterDir + 'Troubleshooting/'
		self.tempDir = 'Temp/'
		self.localTempDir = self.localMasterDir + 'Temp/'

		# LocalFiles
		self.localFirstFrame = self.localMasterDir + self.prepDir + 'FirstDepth.npy'
		self.localLastFrame = self.localMasterDir + self.prepDir + 'LastDepth.npy'
		self.localPiRGB = self.localMasterDir + self.prepDir + 'PiCameraRGB.jpg'
		self.localDepthRGB = self.localMasterDir + self.prepDir + 'DepthRGB.jpg'

		self.localTrayFile = self.localAnalysisDir + 'DepthCrop.txt'
		self.localTransMFile = self.localAnalysisDir + 'TransMFile.npy'
		self.localVideoCropFile = self.localAnalysisDir + 'VideoCrop.npy'
		self.localVideoPointsFile = self.localAnalysisDir + 'VideoPoints.npy'
		self.localSmoothDepthFile = self.localAnalysisDir + 'smoothedDepthData.npy'

		self.localRawDepthFile = self.localTroubleshootingDir + 'rawDepthData.npy'
		self.localInterpDepthFile = self.localTroubleshootingDir + 'interpDepthData.npy'

		self.localPrepSummaryFigure = self.localFigureDir + 'PrepSummary.pdf' 

	def _createParameters(self):
		self.hourlyThreshold = 0.2
		self.dailyThreshold = 0.4
		self.totalThreshold = 1.0
		self.hourlyMinPixels = 1000
		self.dailyMinPixels = 1000
		self.totalMinPixels = 1000
		self.pixelLength = 0.1030168618 # cm / pixel
		self.bowerIndexFraction = 0.1

	def _identifyPiDirectory(self):
		writableDirs = []
		try:
			possibleDirs = os.listdir('/media/pi')
		except FileNotFoundError:
			return

		for d in possibleDirs:

			try:
				with open('/media/pi/' + d + '/temp.txt', 'w') as f:
					print('Test', file = f)
				with open('/media/pi/' + d + '/temp.txt', 'r') as f:
					for line in f:
						if 'Test' in line:
							writableDirs.append(d)
			except:
				pass
			try:
				os.remove('/media/pi/' + d + '/temp.txt')
			except FileNotFoundError:
				continue
		
		if len(writableDirs) == 1:
			self.localMasterDir = '/media/pi/' + d + '/' + self.projectID + '/'
			self.system = 'pi'
		elif len(writableDirs) == 0:
			raise Exception('No writable drives in /media/pi/')
		else:
			raise Exception('Multiple writable drives in /media/pi/. Options are: ' + str(writableDirs))

	def _createDirectory(self, directory):
		if not os.path.exists(directory):
			os.makedirs(directory)

	def _downloadFile(self, dfile):
		subprocess.call(['rclone', 'copy', self.cloudMasterDir + dfile, self.localMasterDir], stderr = self.errorLog)
		if not os.path.exists(self.localMasterDir + dfile):
			raise FileNotFoundError('Unable to download ' + dfile + ' from ' + self.cloudMasterDir)

	def _downloadDirectory(self, directory):

		# First try to download tarred Directory
		tar_directory = directory[:-1] + '.tar'
		subprocess.run(['rclone', 'copy', self.cloudMasterDir + tar_directory, self.localMasterDir], stderr = self.errorLog)
		if os.path.exists(self.localMasterDir + tar_directory):
			print(['tar', '-xvf', self.localMasterDir + tar_directory, '-C', self.localMasterDir])
			subprocess.run(['tar', '-xvf', self.localMasterDir + tar_directory, '-C', self.localMasterDir], stderr = self.errorLog)
			if not os.path.exists(self.localMasterDir + directory):
				raise FileNotFoundError('Unable to untar ' + tar_directory)
			else:
				subprocess.run(['rm', '-f', self.localMasterDir + tar_directory])

		else:
			subprocess.run(['rclone', 'copy', self.cloudMasterDir + directory, self.localMasterDir + directory], stderr = self.errorLog)
			if not os.path.exists(self.localMasterDir + directory):
				raise FileNotFoundError('Unable to download ' + directory + ' from ' + self.cloudMasterDir)

	def _uploadDirectory(self, directory):
		command = ['rclone', 'copy', self.localMasterDir + directory, self.cloudMasterDir + directory]
		output = subprocess.run(command, stdout = subprocess.PIPE, stderr = subprocess.PIPE, encoding = 'utf-8')
		if output.stderr != '':
			print(command)
			print(output.stderr)
			pdb.set_trace()
			raise Exception('rclone was not able to sync ' + directory)
