import pandas as pd
import os, subprocess, sys, collections, pdb
from Modules.FileManager import FileManager as FM

class MasterAnalysisSummary:
	def __init__(self):
		self.fileManager = FM()
		self.anFileManager = self.fileManager.retAnFileManager()

		self.projectTypes = ['Prep', 'Depth', 'Video', 'ML', 'Registration', 'Figures']

	def downloadAnalysisDir(self):
		self.anFileManager.downloadAnalysisDir()

	def uploadAnalysisDir(self):
		self.anFileManager.backupAnalysisDir()

	def deleteAnalysisDir(self):
		subprocess.run(['rm','-rf',self.anFileManager.localMasterDir])

	def addNewProjects(self):

		self._loadAnalysisSummaryFile()

		necessaryFiles = ['Logfile.txt', 'Frames.tar', 'Videos/', 'PrepFiles/DepthRGB.jpg', 'PrepFiles/FirstDepth.npy', 'PrepFiles/LastDepth.npy', 'PrepFiles/PiCameraRGB.jpg']
		goodProjects = set()

		if os.path.exists(self.fileManager.mountedDropboxMasterDir):
			print('Collecting directories using locally mounted Dropbox', file = sys.stderr)

			root, subdirs, files = next(os.walk(self.fileManager.mountedDropboxMasterDir)) # Get first set of directories in master file
	
			for projectID in subdirs:
				goodProject = True
				for nFile in necessaryFiles:
					if not os.path.exists(self.fileManager.mountedDropboxMasterDir + projectID + '/' + nFile):
						goodProject = False

				if goodProject:
					goodProjects.add(projectID)
		else:
			print('Collecting directories using rclone', file = sys.stderr)
		
			projectData = subprocess.run(['rclone', 'lsf', '-R', '--max-depth', '3', self.fileManager.cloudMasterDir], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
			projectData = projectData.stdout.decode().split('\n')

			potentialProjects = set()
			for directory in projectData:
				potentialProjects.add(directory.split('/')[0])

			for projectID in sorted(potentialProjects):
				necessaryFiles = [projectID + '/' + x for x in baseFileNames]
				goodProject = True
			
				for nFile in necessaryFiles:
					if nFile not in projectData:
						goodProject = False

				if goodProject:
					goodProjects.add(projectID)

		analysisData = collections.defaultdict(list)
		projectIDs = []
		for projectID in sorted(goodProjects):
			if projectID not in self.anDT.index:
				projectIDs.append(projectID)
				analysisData['Prep_Version'].append('None')
				analysisData['Prep_Date'].append('None')

				analysisData['Depth_Version'].append('None')
				analysisData['Depth_Date'].append('None')
				
				analysisData['Video_Version'].append('None')
				analysisData['Video_Date'].append('None')

				analysisData['MachineLearning_Version'].append('None')
				analysisData['MachineLearning_Date'].append('None')

				analysisData['Registration_Version'].append('None')
				analysisData['Registration_Date'].append('None')

				analysisData['Figures_Version'].append('None')
				analysisData['Figures_Date'].append('None')
		
		dt = pd.DataFrame(analysisData, index = sorted(projectIDs))
		self.anDT.append(dt)

		self.anDT.to_excel(self.anFileManager.localAnalysisSummaryFile, sheet_name = 'Master', index = True)  # doctest: +SKIP

	def mergeUpdates(self):

		updateFiles = [x for x in os.listdir(self.anFileManager.localMasterDir) if 'AnalysisUpdate' in x]
		updateDTs = []
		for update in updateFiles:
			updateDTs.append(pd.read_csv(self.anFileManager.localMasterDir + update, sep = ','))
		allUpdates = pd.concat(updateDTs)
		allUpdates.Date = pd.to_datetime(allUpdates.Date, format = '%Y-%m-%d %H:%M:%S.%f')
		allUpdates = allUpdates.sort_values(['ProjectID', 'Date']).groupby(['ProjectID','Type']).last()
		for index, row in allUpdates.iterrows():
			self.anDT.loc[index[0],index[1] + '_Version'] = row.Version
			self.anDT.loc[index[0],index[1] + '_Date'] = row.Date

		self.anDT.to_excel(self.anFileManager.localAnalysisSummaryFile, sheet_name = 'Master', index = True)
		for update in updateFiles:
			subprocess.run(['rm', '-f', self.anFileManager.localMasterDir + update])
			subprocess.run(['rclone', 'delete', self.anFileManager.cloudMasterDir + update])


	def retProjects(self, unRun = None, oldVersion = None):
		try:
			self.anDT
		except AttributeError:
			self._loadAnalysisSummaryFile()

		if unRun is None and oldVersion is None:
			return(list(self.anDT.index))

		elif unRun is not None:
			if unRun not in self.projectTypes:
				raise KeyError('unRun must be one of: ' + str(self.projectTypes))
			else:
				return(list(self.anDT[self.anDT[unRun + '_Date'] == 'None'].index))

		else:
			raise NotImplementedError

	def _loadAnalysisSummaryFile(self):
		self.anDT = pd.read_excel(self.anFileManager.localAnalysisSummaryFile, index_col = 0, sheet_name = 'Master')

