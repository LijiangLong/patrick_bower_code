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

		self.errorLog = open(self.localMasterDir + 'ErrorLog.txt', 'a')

	def preparePrepAnalysis(self):
		self._createDirectory(self.localMasterDir)
		self._createDirectory(self.localAnalysisDir)
		self._createDirectory(self.localFigureDir)
		self._downloadFile(self.logfile)
		self._downloadDirectory(self.prepDir)

	def backupPrepAnalysis(self):
		self._uploadDirectory(self.prepDir)

	def prepareDepthAnalysis(self):
		self._createDirectory(self.localMasterDir)
		self._downloadFile(self.logfile)
		self._downloadDirectory(self.frameDir)

	def _createFileDirectoryNames(self):
		# Create logfile
		self.logfile = 'Logfile.txt'
		self.localLogfile = self.localMasterDir + self.logfile

		# Data directories created by tracker
		self.prepDir = 'PrepFiles/'
		self.frameDir = 'Frames'
		self.backgroundDir = 'Backgrounds'
		self.videoDir = 'Videos'

		# Directories created by analysis scripts
		self.analysisDir = 'Analysis/'
		self.localAnalysisDir = self.localMasterDir + 'Analysis/'
		self.localFigureDir = self.localMasterDir + 'Figures/'
		self.labelClipAnalysis = 'LabelClips/'
		self.mlClipAnalysis = 'MLClips/'
		self.troubleshooting = 'Troubleshooting/'

		# LocalFiles
		self.localFirstFrame = self.localMasterDir + self.prepDir + 'FirstDepth.npy'
		self.localLastFrame = self.localMasterDir + self.prepDir + 'LastDepth.npy'
		self.localPiRGB = self.localMasterDir + self.prepDir + 'PiCameraRGB.jpg'
		self.localDepthRGB = self.localMasterDir + self.prepDir + 'DepthRGB.jpg'

		self.localTrayFile = self.localAnalysisDir + 'DepthCrop.txt'
		self.localTransMFile = self.localAnalysisDir + 'TransMFile.npy'
		self.localVideoCropFile = self.localAnalysisDir + 'VideoCrop.npy'
		self.localVideoPointsFile = self.localAnalysisDir + 'VideoPoints.npy'

		self.localPrepSummaryFigure = self.localFigureDir + 'PrepSummary.pdf' 

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

		subprocess.run(['rclone', 'copy', self.cloudMasterDir + directory, self.localMasterDir + directory], stderr = self.errorLog)
		if not os.path.exists(self.localMasterDir + directory):
			subprocess.run(['rclone', 'copy', self.cloudMasterDir + directory + '.tar', self.localMasterDir], stderr = self.errorLog)
			if not os.path.exists(self.localMasterDir + directory + '.tar'):
				raise FileNotFoundError('Unable to download ' + directory + ' from ' + self.cloudMasterDir)
			else:
				print(['tar', '-xvf', self.localMasterDir + directory + '.tar', '-C', self.localMasterDir])
				subprocess.run(['tar', '-xvf', self.localMasterDir + directory + '.tar', '-C', self.localMasterDir], stderr = self.errorLog)
				if not os.path.exists(self.localMasterDir + directory):
					raise FileNotFoundError('Unable to untar ' + directory + '.tar')
				else:
					subprocess.run(['rm', '-f', self.localMasterDir + directory + '.tar'])

	def _uploadDirectory(self, directory):
		output = subprocess.run(['rclone', 'copy', self.cloudMasterDir + directory, self.localMasterDir + directory], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text = True)
		if output.stderr != '':
			raise Exception('rclone was not able to sync ' + directory)
