import subprocess, pickle, os, shutil, pdb, scipy, datetime
from skimage import io
import pandas as pd


class MLClusterPreparer:
	# This class takes in directory information and a logfile containing depth information and performs the following:
	# 1. Identifies tray using manual input
	# 2. Interpolates and smooths depth data
	# 3. Automatically identifies bower location
	# 4. Analyze building, shape, and other pertinent info of the bower

	def __init__(self, projFileManager, mlFileManager):
		self.__version__ = '1.0.0'

		self.projFileManager = projFileManager
		self.mlFileManager = mlFileManager

	def validateInputData(self):
		assert os.path.exists(self.projFileManager.localAllClipsDir)
		assert os.path.exists(self.projFileManager.localAllLabeledClustersFile)

		assert os.path.exists(self.mlFileManager.localVideoModelFile)
		assert os.path.exists(self.mlFileManager.localVideoClassesFile)
		assert os.path.exists(self.mlFileManager.localVideoCommandsFile)
		assert os.path.exists(self.mlFileManager.localVideoPythonMainFile)
		assert os.path.exists(self.mlFileManager.localVideoPythonJsonFile)
		
		self.uploads = [(self.projFileManager.localAnalysisDir, self.projFileManager.cloudAnalysisDir, 0)
						]

	def predictVideoLabels(self):
		self._identifyVideoClasses()
		self._prepareClips()
		self._predictLabels()

	def _identifyVideoClasses(self):
		self.videoClasses = []
		with open(self.mlFileManager.localVideoClassesFile) as f:
			for line in f:
				tokens = line.rstrip().split()
				self.videoClasses.append(tokens[1])

	def _prepareClips(self):
		print('Converting clips into jpgs and calculating means,,Time: ' + str(datetime.datetime.now())) 

		clips = [x for x in os.listdir(self.projFileManager.localAllClipsDir) if '.mp4' in x]
		assert len(clips) != 0

		with open(self.projFileManager.localProcessedClipsDir + 'MeansAll.csv', 'w') as f, open(self.projFileManager.localProcessedClipsDir + 'cichlids_test_list.txt', 'w') as g:
			print('Clip,MeanR,MeanG,MeanB,StdR,StdG,StdB', file = f)
			for clip in clips:
				label = self.videoClasses[0] # Need to temporarily assign the clip to a label - just pick the first
					
				outDirectory = self.projFileManager.localProcessedClipsDir + label + '/' + clip.replace('.mp4','') + '/'

				shutil.rmtree(outDirectory) if os.path.exists(outDirectory) else None
				os.makedirs(outDirectory) 

				outdata = subprocess.run(['ffmpeg', '-i', self.projFileManager.localAllClipsDir + clip, outDirectory + 'image_%05d.jpg'], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
				#print(['ffmpeg', '-i', self.projFileManager.localAllClipsDir + clip, outDirectory + 'image_%05d.jpg'])

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
				print(self.projFileManager.processedClipDir + '/' + label + '/' + clip.replace('.mp4',''), file = g)

		subprocess.run(['touch', self.projFileManager.localProcessedClipsDir + 'cichlids_train_list.txt'])


		dt = pd.read_csv(self.projFileManager.localProcessedClipsDir + 'MeansAll.csv', sep = ',')
		dt['MeanID'] = dt.apply(lambda row: row.Clip.split('__')[0], axis = 1)
		means = dt.groupby('MeanID').mean()

		with open(self.projFileManager.localProcessedClipsDir + 'Means.csv', 'w') as f:
			print('meanID,redMean,greenMean,blueMean,redStd,greenStd,blueStd', file = f)
			for row in means.itertuples():
				print(row.Index + ',' + str(row.MeanR) + ',' + str(row.MeanG) + ',' + str(row.MeanB) + ',' + str(row.StdR) + ',' + str(row.StdG) + ',' + str(row.StdB), file = f)

		with open(self.projFileManager.localProcessedClipsDir + 'AnnotationFile.csv', 'w') as f:
			print('Location,Dataset,Label,MeanID', file = f)
			for row in dt.itertuples():
				print(row.Clip + ',Test,' + label + ',' + row.MeanID, file = f)


		command = []
		command += ['python3', self.mlFileManager.localVideoPythonJsonFile]
		command += [self.mlFileManager.localVideoClassesFile]
		command += [self.projFileManager.localProcessedClipsDir + 'cichlids_train_list.txt']
		command += [self.projFileManager.localProcessedClipsDir + 'cichlids_test_list.txt']
		command += [self.projFileManager.localMasterDir + 'cichlids.json']
		subprocess.call(command)

	def _predictLabels(self):

		print('Predicting labels for each video and merging information into ClusterSummary,,Time: ' + str(datetime.datetime.now())) 

		# Load command file
		with open(self.mlFileManager.localVideoCommandsFile, 'rb') as pickle_file:
			command = pickle.load(pickle_file) 
		
		command['--root_path'] = self.projFileManager.localMasterDir
		command['--n_epochs'] = '1'
		command['--pretrain_path'] = self.mlFileManager.localVideoModelFile
		command['--mean_file'] = self.projFileManager.localProcessedClipsDir + 'Means.csv'
		command['--annotation_file'] = self.projFileManager.localProcessedClipsDir + 'AnnotationFile.csv'
		command['--annotation_path'] = 'cichlids.json'
		command['--batch_size'] = str(int(int(command['--batch_size'])*2))
		command['--video_path'] = 'AllClips'

		resultsDirectory = 'prediction/'
		shutil.rmtree(self.projFileManager.localMasterDir + resultsDirectory) if os.path.exists(self.projFileManager.localMasterDir + resultsDirectory) else None
		os.makedirs(self.projFileManager.localMasterDir + resultsDirectory) 

		trainEnv = os.environ.copy()
		trainEnv['CUDA_VISIBLE_DEVICES'] = str(6)
		command['--result_path'] = resultsDirectory

		#pickle.dump(command, open(self.localOutputDirectory + 'commands.pkl', 'wb'))

		outCommand = []
		[outCommand.extend([str(a),str(b)]) for a,b in zip(command.keys(), command.values())] + ['--no_train']
		
		outdata = subprocess.run(outCommand, env = trainEnv, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		print(outdata.stderr)

		dt = pd.read_csv(self.projFileManager.localMasterDir + '/prediction/ConfidenceMatrix.csv', header = None, names = ['Filename'] + self.videoClasses, skiprows = [0], index_col = 0)
		softmax = dt.apply(scipy.special.softmax, axis = 1)
		prediction = pd.concat([softmax.idxmax(axis=1).rename(self.mlFileManager.vModelID + '_pred'), softmax.max(axis=1).rename(self.mlFileManager.vModelID + '_conf')], axis=1)
		prediction['ClipName'] = prediction.apply(lambda row: row.name.split('/')[-1], axis = 1)
		allClusterData = pd.read_csv(self.projFileManager.localAllLabeledClustersFile, sep = ',')
		allClusterData = pd.merge(allClusterData, prediction, how = 'left', left_on = 'ClipName', right_on = 'ClipName')
		allClusterData.to_csv(self.projFileManager.localAllLabeledClustersFile, sep = ',')

		print('ML cluster classification complete,,Time: ' + str(datetime.datetime.now())) 

