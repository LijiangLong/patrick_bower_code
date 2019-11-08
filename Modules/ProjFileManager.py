import os, subprocess, pdb


class ProjFileManager():
	def __init__(self, localMasterDir, cloudMasterDir, projectID):
		self.projectID = projectID

		self.localMasterDir = localMasterDir + projectID + '/'
		self.cloudMasterDir = cloudMasterDir + projectID + '/'
		

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

	def prepareClusterAnalysis(self):
		self._createDirectory(self.localTroubleshootingDir)
		self._createDirectory(self.localFigureDir)
		self._createDirectory(self.localTempDir)
		self._createDirectory(self.localAllClipsDir)
		self._createDirectory(self.localManualLabelClipsDir)
		self._createDirectory(self.localManualLabelFramesDir)

		self._downloadFile(self.logfile)
		self._downloadDirectory(self.videoDir)
		
	def backupClusterAnalysis(self):
		self._uploadDirectory(self.analysisDir)
		self._uploadDirectory(self.troubleshootingDir)
		self._uploadDirectory(self.figureDir)
		self._uploadDirectory(self.allClipsDir, tar = True)
		self._uploadDirectory(self.manualLabelClipsDir, tar = True)
		self._uploadDirectory(self.manualLabelFramesDir, tar = True)

	def prepareMLVideoAnalysis(self):
		self._createDirectory(self.localMasterDir)
		self._createDirectory(self.localProcessedClipsDir)

		self._downloadFile(self.logfile)
		self._downloadDirectory(self.analysisDir)
		self._downloadDirectory(self.allClipsDir)


	def prepareFigureAnalysis(self):
		self._createDirectory(self.localMasterDir)
		self._createDirectory(self.localFigureDir)
		self._downloadFile(self.logfile)
		self._downloadDirectory(self.analysisDir)

	def backupFigureAnalysis(self):
		self._uploadDirectory(self.figureDir)

	def localDelete(self):
		subprocess.run(['rm','-rf', self.localMasterDir])

	def returnVideoObject(self, index):
		from Modules.LogParser import LogParser as LP

		self._downloadFile(self.logfile)
		self.lp = LP(self.localLogfile)
		videoObj = self.lp.movies[index]
		videoObj.localVideoFile = self.localMasterDir + videoObj.mp4_file
		videoObj.localHMMFile = self.localTroubleshootingDir + videoObj.baseName + '.hmm'
		videoObj.localRawCoordsFile = self.localTroubleshootingDir + videoObj.baseName + '_rawCoords.npy'
		videoObj.localLabeledCoordsFile = self.localTroubleshootingDir + videoObj.baseName + '_labeledCoords.npy'
		videoObj.localLabeledClustersFile = self.localTroubleshootingDir + videoObj.baseName + '_labeledClusters.csv'
		videoObj.localAllClipsPrefix = self.localAllClipsDir + self.lp.projectID + '_' + videoObj.baseName
		videoObj.localManualLabelClipsPrefix = self.localManualLabelClipsDir + self.lp.projectID + '_' + videoObj.baseName
		videoObj.localIntensityFile = self.localFigureDir + videoObj.baseName + '_intensity.pdf'
		videoObj.localTempDir = self.localTempDir + videoObj.baseName + '/'
		self._createDirectory(videoObj.localTempDir)

		return videoObj

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
		self.allClipsDir = 'AllClips/'
		self.localAllClipsDir = self.localMasterDir + 'AllClips/'
		self.processedClipDir = 'ProcessedClips/'
		self.localProcessedClipsDir = self.localMasterDir + 'AllClips/'
		self.manualLabelClipsDir = 'MLClips/'
		self.localManualLabelClipsDir = self.localMasterDir + 'MLClips/'
		self.manualLabelFramesDir = 'MLFrames/'
		self.localManualLabelFramesDir = self.localMasterDir + 'MLFrames/'

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
		self.localRGBDepthVideo = self.localAnalysisDir + 'DepthRGBVideo.mp4'

		self.localRawDepthFile = self.localTroubleshootingDir + 'rawDepthData.npy'
		self.localInterpDepthFile = self.localTroubleshootingDir + 'interpDepthData.npy'

		self.localPrepSummaryFigure = self.localFigureDir + 'PrepSummary.pdf' 

		self.localAllLabeledClustersFile = self.localAnalysisDir + 'AllLabeledClusters.csv'

	def _createParameters(self):

		# Depth related parameters
		self.hourlyThreshold = 0.2
		self.dailyThreshold = 0.4
		self.totalThreshold = 1.0
		self.hourlyMinPixels = 1000
		self.dailyMinPixels = 1000
		self.totalMinPixels = 1000
		self.pixelLength = 0.1030168618 # cm / pixel
		self.bowerIndexFraction = 0.1

		# Video related parameters
		self.lightsOnTime = 8
		self.lightsOffTime = 18

		# DB Scan related parameters
		self.minMagnitude = 0
		self.treeR = 22 
		self.leafNum = 190 
		self.neighborR = 22
		self.timeScale = 10
		self.eps = 18
		self.minPts = 90 
		self.delta = 1.0 # Batches to calculate clusters

		# Clip creation parameters
		self.nManualLabelClips = 400
		self.delta_xy = 100
		self.delta_t = 60
		self.smallLimit = 500

		# Manual Label Frame 
		self.nManualLabelFrames = 200


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

	def _uploadDirectory(self, directory, tar = False):
		if tar:
			if directory[-1] == '/':
				directory = directory[:-1]
			subprocess.run(['tar', '-cvf', self.localMasterDir + directory + '.tar', '-C', self.localMasterDir, directory], stderr = self.errorLog)
			command = ['rclone', 'copy', self.localMasterDir + directory + '.tar', self.cloudMasterDir, '--exclude', '.DS_Store']
		else:
			command = ['rclone', 'copy', self.localMasterDir + directory, self.cloudMasterDir + directory, '--exclude', '.DS_Store']
	
		output = subprocess.run(command, stdout = subprocess.PIPE, stderr = subprocess.PIPE, encoding = 'utf-8')
		if output.stderr != '':
			print(command)
			print(output.stderr)
			pdb.set_trace()
			raise Exception('rclone was not able to sync ' + directory)
