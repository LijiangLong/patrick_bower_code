import pandas as pd
import os, subprocess, sys, pdb, collections
from Modules.FileManagers.FileManager import FileManager as FM

class AnalysisPreparer:
	def __init__(self):
		__version__ = '1.0.0'
		self.fileManager = FM()
		self.projectTypes = ['Prep', 'Depth', 'Cluster', 'MLCluster', 'MLObject', 'Figures']

	def updateAnalysisFile(self, newProjects = True, projectSummary = True):
		self._loadAnalysisDir()
		if newProjects:
			self._identifyNewProjects()
		self._mergeUpdates()
		if projectSummary:
			self._createProjectsSummary()
		self.fileManager.uploadData(self.fileManager.localAnalysisSummaryFile, self.fileManager.localAnalysisLogDir, False)

	def checkProjects(self, projects):
		self._loadAnalysisDir()
		self._createProjectsSummary(print_screen = False)
		badProject = False
		for project in projects:
			if project not in self.info['All']:
				print(project + ' not a valid project')
				badProject = True
		return badProject

	def _loadAnalysisDir(self):
		self.fileManager.downloadDirectory(self.fileManager.analysisDir)
		self.anDT = pd.read_excel(self.fileManager.localAnalysisSummaryFile, index_col = 0, sheet_name = 'Master')

	def _identifyNewProjects(self):
		necessaryFiles = ['Logfile.txt', 'Frames.tar', 'Videos/', 'PrepFiles/DepthRGB.jpg', 'PrepFiles/FirstDepth.npy', 'PrepFiles/LastDepth.npy', 'PrepFiles/PiCameraRGB.jpg']
		goodProjects = set()

		if os.path.exists(self.fileManager.mountedDropboxMasterDir):
			print('Collecting directories using locally mounted Dropbox')

			root, subdirs, files = next(os.walk(self.fileManager.mountedDropboxMasterDir)) # Get first set of directories in master file
	
			for projectID in subdirs:
				goodProject = True
				for nFile in necessaryFiles:
					if not os.path.exists(self.fileManager.mountedDropboxMasterDir + projectID + '/' + nFile):
						goodProject = False

				if goodProject:
					goodProjects.add(projectID)
		else:
			print('Collecting directories using rclone')
		
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
				
				analysisData['Cluster_Version'].append('None')
				analysisData['Cluster_Date'].append('None')

				analysisData['MLCluster_Version'].append('None')
				analysisData['MLCluster_Date'].append('None')

				analysisData['MLObject_Version'].append('None')
				analysisData['MLObject_Date'].append('None')

				analysisData['Figures_Version'].append('None')
				analysisData['Figures_Date'].append('None')
		
		dt = pd.DataFrame(analysisData, index = sorted(projectIDs))
		self.anDT.append(dt)

		self.anDT.to_excel(self.fileManager.localAnalysisSummaryFile, sheet_name = 'Master', index = True)  # doctest: +SKIP

	def _mergeUpdates(self):

		updateFiles = [x for x in os.listdir(self.fileManager.localAnalysisLogDir) if 'AnalysisUpdate' in x]
		if updateFiles == []:
			return
		updateDTs = []
		for update in updateFiles:
			updateDTs.append(pd.read_csv(self.fileManager.localAnalysisLogDir + update, sep = ','))
		allUpdates = pd.concat(updateDTs)
		allUpdates.Date = pd.to_datetime(allUpdates.Date, format = '%Y-%m-%d %H:%M:%S.%f')
		allUpdates = allUpdates.sort_values(['ProjectID', 'Date']).groupby(['ProjectID','Type']).last()
		for index, row in allUpdates.iterrows():
			self.anDT.loc[index[0],index[1] + '_Version'] = row.Version
			self.anDT.loc[index[0],index[1] + '_Date'] = row.Date

		self.anDT.to_excel(self.fileManager.localAnalysisSummaryFile, sheet_name = 'Master', index = True)
		for update in updateFiles:
			subprocess.run(['rm', '-f', self.fileManager.localAnalysisLogDir + update])
			subprocess.run(['rclone', 'delete', self.fileManager.cloudAnalysisLogDir + update])


	def _createProjectsSummary(self, print_screen = True):
		self.info = {}
		self.info['All'] = list(self.anDT.index)
		for analysis in self.projectTypes:
			self.info[analysis] = list(self.anDT[self.anDT[analysis + '_Version'] == 'None'].index)

		if print_screen:
			print('AllProjects: ' + ','.join(self.info['All']))
			for analysis in self.projectTypes:
				print('Unanalyzed ' + analysis + ': ' + ','.join(self.info[analysis]))


