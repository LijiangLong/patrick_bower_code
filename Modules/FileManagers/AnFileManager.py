import os, subprocess, pdb
import pandas as pd

class AnFileManager():
	def __init__(self, localMasterDir, cloudMasterDir):
		self.annotationDir = '__AnnotatedData/'
		self.localMasterDir = localMasterDir + self.annotationDir
		self.cloudMasterDir = cloudMasterDir + self.annotationDir

	def prepareVideoAnnotation(self, annotationID):
		self.cloudClipDir = self.cloudMasterDir + 'LabeledVideos/' + annotationID + '/'
		self.localClipDir = self.localMasterDir + 'LabeledVideos/' + annotationID + '/'
		
		# Download clip dir
		subprocess.run(['rclone', 'copy', self.cloudClipDir, self.localClipDir], stderr = subprocess.PIPE)
		if not os.path.exists(self.localClipDir):
			raise FileNotFoundError('Unable to download ' + self.cloudClipDir)

		# Untar clips
		for tarredClipDir in [self.localClipDir + 'Clips/' + x for x in os.listdir(self.localClipDir + 'Clips/') if '.tar' in x]:
			subprocess.run(['tar', '-xvf', tarredClipDir, '-C', self.localClipDir + 'Clips/'], stderr = subprocess.PIPE)
			subprocess.run(['rm', '-f', tarredClipDir])

		
		# Read in manual annotations
		dt = pd.read_csv(self.localClipDir + 'ManualLabels.csv', sep = ',')

		# Iterate through manual annotations and keep track of 
		for index, row in dt.iterrows():
			projectID = row.ClipName.split('__')[0]
			clipName = row.ClipName + '.mp4'
			label = row.ManualLabel
			os.makedirs(self.localClipDir + 'LabeledClips/' + label, exist_ok = True)
			output = subprocess.run(['mv', self.localClipDir + 'Clips/' + projectID + '/' + clipName, self.localClipDir + 'LabeledClips/' +  label], stderr = subprocess.PIPE, encoding = 'utf-8')
			if output.stderr != '':
				print(clipName)

		return self.localClipDir + 'LabeledClips/'
