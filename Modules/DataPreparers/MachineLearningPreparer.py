import subprocess, pickle, os, shutil, pdb
from skimage import io
import pandas as pd


class MachineLearningPreparer:
	# This class takes in directory information and a logfile containing depth information and performs the following:
	# 1. Identifies tray using manual input
	# 2. Interpolates and smooths depth data
	# 3. Automatically identifies bower location
	# 4. Analyze building, shape, and other pertinent info of the bower

	def __init__(self, projFileManager):
		self.prFileManager = projFileManager

	def predictVideoLabels(self, mlFileManager):
		self.mlFileManager = mlFileManager
		self._identifyVideoClasses()
		self._prepareClips()
		self._predictLabels()
		return self.predictions

	def _identifyVideoClasses(self):
		self.videoClasses = []
		with open(self.mlFileManager.localVideoClassesFile) as f:
			for line in f:
				tokens = line.rstrip().split()
				self.videoClasses.append(tokens[1])

	def _prepareClips(self):

		clips = [x for x in os.listdir(self.prFileManager.localAllClipsDir) if '.mp4' in x]
		assert len(clips) != 0

		with open(self.prFileManager.localMasterDir + 'MeansAll.csv', 'w') as f, open(self.prFileManager.localMasterDir + 'cichlids_test_list.txt', 'w') as g:
			print('Clip,MeanR,MeanG,MeanB,StdR,StdG,StdB', file = f)
			for clip in clips:
				label = self.videoClasses[0] # Need to temporarily assign the clip to a label - just pick the first
					
				outDirectory = self.prFileManager.localProcessedClipsDir + label + '/' + clip.replace('.mp4','') + '/'

				#shutil.rmtree(outDirectory) if os.path.exists(outDirectory) else None
				#os.makedirs(outDirectory) 

				#outdata = subprocess.run(['ffmpeg', '-i', self.prFileManager.localAllClipsDir + clip, outDirectory + 'image_%05d.jpg'], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
				#print(['ffmpeg', '-i', self.prFileManager.localAllClipsDir + clip, outDirectory + 'image_%05d.jpg'])

				frames = [x for x in os.listdir(outDirectory) if '.jpg' in x]
				try:
					if self.nFrames != len(frames):
						raise Exception('Different number of frames than expected in: ' + clip)
				except AttributeError:
					self.nFrames = len(frames)

					with open(outDirectory + 'n_frames', 'w') as i:
						print(str(self.nFrames), file = i)

				img = io.imread(outDirectory + frames[0])
				mean = img.mean(axis = (0,1))
				std = img.std(axis = (0,1))
				print(clip.replace('.mp4', '') + ',' + ','.join([str(x) for x in mean]) + ',' + ','.join([str(x) for x in std]), file = f)
				print(label + '/' + clip.replace('.mp4',''), file = g)

		subprocess.run(['touch', self.prFileManager.localMasterDir + 'cichlids_train_list.txt'])


		dt = pd.read_csv(self.prFileManager.localMasterDir + 'MeansAll.csv', sep = ',')
		dt['MeanID'] = dt.apply(lambda row: row.Clip.split('__')[0], axis = 1)
		means = dt.groupby('MeanID').mean()

		with open(self.prFileManager.localMasterDir + 'Means.csv', 'w') as f:
			print('meanID,redMean,greenMean,blueMean,redStd,greenStd,blueStd', file = f)
			for row in means.itertuples():
				print(row.Index + ',' + str(row.MeanR) + ',' + str(row.MeanG) + ',' + str(row.MeanB) + ',' + str(row.StdR) + ',' + str(row.StdG) + ',' + str(row.StdB), file = f)

		with open(self.prFileManager.localMasterDir + 'AnnotationFile.csv', 'w') as f:
			print('Location,Dataset,Label,MeanID', file = f)
			for row in dt.itertuples():
				print(row.Clip + ',Test,' + label + ',' + row.MeanID, file = f)


		command = []
		command += ['python3', self.mlFileManager.localVideoPythonJsonFile]
		command += [self.mlFileManager.localVideoClassesFile]
		command += [self.prFileManager.localMasterDir + 'cichlids_train_list.txt']
		command += [self.prFileManager.localMasterDir + 'cichlids_test_list.txt']
		command += [self.prFileManager.localMasterDir + 'cichlids.json']
		print(command)
		subprocess.call(command)

	def _predictLabels(self):

		# Load command file
		with open(self.mlFileManager.localVideoCommandsFile, 'rb') as pickle_file:
			command = pickle.load(pickle_file) 
		
		command['--root_path'] = self.prFileManager.localMasterDir
		command['--n_epochs'] = '1'
		command['--pretrain_path'] = self.mlFileManager.localVideoModelFile
		command['--mean_file'] = self.prFileManager.localMasterDir + 'Means.csv'
		command['--annotation_file'] = self.prFileManager.localMasterDir + 'AnnotationFile.csv'
		command['--annotation_path'] = 'cichlids.json'
		command['--batch_size'] = str(int(int(command['--batch_size'])*2))

		resultsDirectory = 'prediction/'
		shutil.rmtree(self.prFileManager.localMasterDir + resultsDirectory) if os.path.exists(self.prFileManager.localMasterDir + resultsDirectory) else None
		os.makedirs(self.prFileManager.localMasterDir + resultsDirectory) 

		trainEnv = os.environ.copy()
		trainEnv['CUDA_VISIBLE_DEVICES'] = str(5)
		command['--result_path'] = resultsDirectory

		#pickle.dump(command, open(self.localOutputDirectory + 'commands.pkl', 'wb'))

		outCommand = []
		[outCommand.extend([str(a),str(b)]) for a,b in zip(command.keys(), command.values())] + ['--no_train']
		
		outdata = subprocess.run(outCommand, env = trainEnv, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		print(outdata.stdout)

		dt = pd.read_csv(self.prFileManager.localMasterDir + '/prediction/ConfidenceMatrix.csv', header = None, names = ['Filename'] + self.videoClasses, skiprows = [0], index_col = 0)
		softmax = dt.apply(scipy.special.softmax, axis = 1)
		prediction = pd.concat([softmax.idxmax(axis=1).rename(modelID + '_pred'), softmax.max(axis=1).rename(modelID + '_conf')], axis=1)

		allClusterData = pd.read_csv(self.projFileManager.localAllLabeledClustersFile, sep = ',')
		allClusterData = pd.merge(allClusterData, prediction, how = 'left_outer', left_on = 'ClipName', right_on = 'ClipName')
		allClusterData.to_csv(self.projFileManager.localAllLabeledClustersFile, sep = ',')


