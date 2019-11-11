from Modules.LogParser import LogParser as LP
from Modules.DataObjects.HMMAnalyzer import HMMAnalyzer as HA
from multiprocessing.dummy import Pool as ThreadPool
from sklearn.cluster import DBSCAN
from sklearn.neighbors import radius_neighbors_graph
from sklearn.neighbors import NearestNeighbors

import numpy as np
import pandas as pd
import os, cv2, math, datetime, subprocess, pdb, random

class VideoPreparer:
	# This class takes in directory information and a logfile containing depth information and performs the following:
	# 1. Identifies tray using manual input
	# 2. Interpolates and smooths depth data
	# 3. Automatically identifies bower location
	# 4. Analyze building, shape, and other pertinent info of the bower

	def __init__(self, projFileManager, index, workers):
		self.projFileManager = projFileManager
		self.lp = LP(self.projFileManager.localLogfile)

		self.videoObj = self.projFileManager.returnVideoObject(index)
		self.videofile = self.videoObj.localVideoFile
		self.workers = workers

		self.lightsOnTime = self.videoObj.startTime.replace(hour = self.projFileManager.lightsOnTime, minute = 0, second = 0, microsecond = 0)
		self.lightsOffTime = self.videoObj.startTime.replace(hour = self.projFileManager.lightsOffTime, minute = 0, second = 0, microsecond = 0)

		self.HMMsecs = int((min(self.videoObj.endTime, self.lightsOffTime) - self.videoObj.startTime).total_seconds() - 1)

	def processVideo(self):
		self._validateVideo()
		self._decompressVideo()
		self._calculateHMM()
		self._createClusters()
		self._createAnnotationFiles()

		return self.clusterData

	def _validateVideo(self, tol = 0.001):
		if not os.path.isfile(self.videofile):
			self._convertVideo(self.videofile)
		assert os.path.isfile(self.videofile)
		
		cap = cv2.VideoCapture(self.videofile)
		new_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
		new_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
		new_framerate = cap.get(cv2.CAP_PROP_FPS)
		new_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
		predicted_frames = int((self.videoObj.endTime - self.videoObj.startTime).total_seconds()*self.videoObj.framerate)

		print('VideoValidation: Size: ' + str((new_height,new_width)) + ',,fps: ' + str(new_framerate) + ',,Frames: ' + str(new_frames) + ',,PredictedFrames: ' + str(predicted_frames))

		assert new_height == self.videoObj.height
		assert new_width == self.videoObj.width
		assert abs(new_framerate - self.videoObj.framerate) < tol*self.videoObj.framerate
		assert abs(predicted_frames - new_frames) < tol*predicted_frames

		self.frames = new_frames

		cap.release()

	def _convertVideo(self, mp4_video):
		h264_video = mp4_video.replace('.mp4', '.h264')
		assert os.path.isfile(h264_video)

		command = ['ffmpeg', '-r', str(self.videoObj.framerate), '-i', h264_video, '-c:v', 'copy', '-r', str(self.videoObj.framerate), mp4_video]
		print('VideoConversion: ' + ' '.join(command) + ',Time' + str(datetime.datetime.now()))
		output = subprocess.run(command, stdout = subprocess.PIPE, stdin = subprocess.PIPE)
		assert os.path.isfile(mp4_video)

		# Ensure the conversion went ok.     
		assert os.stat(mp4_video).st_size >= os.stat(h264_video).st_size


	def _decompressVideo(self):

		# Don't process videos when the lights are dimmed (>6pm)
		self.blocksize = 5*60 # Decompress videos in 5 minute chunks

		totalBlocks = math.ceil(self.HMMsecs/(self.blocksize)) #Number of blocks that need to be analyzed for the full video
		print('Decompressing video into 1 second chunks,,Time: ' + str(datetime.datetime.now()))
		print(str(totalBlocks) + ' total blocks. On block ', end = '', flush = True)
		"""
		for i in range(0, totalBlocks, self.workers):
			print(str(i) + '-' + str(i+self.workers) + ',', end = '', flush = True)
			processes = []
			for j in range(self.workers):
				min_time = int((i+j)*self.blocksize)
				max_time = int(min((i+j+1)*self.blocksize, self.HMMsecs))
				
				arguments = [self.videofile, str(self.videoObj.framerate), str(min_time), str(max_time), self.videoObj.localTempDir + 'Decompressed_' + str(i+j) + '.npy']
				processes.append(subprocess.Popen(['python3', 'Modules/Scripts/Decompress_block.py'] + arguments))
			
			for p in processes:
				p.communicate()
		"""
		print()
		print('Combining data into rowfiles,,Time: ' + str(datetime.datetime.now()))
		for row in range(self.videoObj.height):
			row_file = self.videoObj.localTempDir + str(row) + '.npy'
			if os.path.isfile(row_file):
				subprocess.run(['rm', '-f', row_file])
		print(str(totalBlocks) + ' total blocks. On block: ', end = '', flush = True)
		for i in range(0, totalBlocks, self.workers):
			print(str(i) + '-' + str(i+self.workers) + ',', end = '', flush = True)
			data = []
			for j in range(self.workers):
				block = i + j

				data.append(np.load(self.videoObj.localTempDir + 'Decompressed_' + str(block) + '.npy'))

			alldata = np.concatenate(data, axis = 1)

			for row in range(self.videoObj.height):
				row_file = self.videoObj.localTempDir + str(row) + '.npy'
				out_data = alldata[row]
				if os.path.isfile(row_file):
					out_data = np.concatenate([np.load(row_file),out_data], axis = 1)
					pdb.set_trace()
				np.save(row_file, out_data)

				# Verify size is right
				if block + 1 == totalBlocks:
					assert out_data.shape != (self.videoObj.width, self.HMMsecs)
			#subprocess.run(['rm', '-f', self.videoObj.localTempDir + 'Decompressed_' + str(block) + '.npy'])


	def _calculateHMM(self):
		totalBlocks = math.ceil(self.videoObj.height/self.workers)
		print('Calculating HMMs for each row,,Time: ' + str(datetime.datetime.now())) 
		# Calculate HMM on each block
		for block in range(0, totalBlocks):
			start_row = block*self.workers
			stop_row = min((block+1)*self.workers,self.videoObj.height)
			print(str(start_row) + '-' + str(stop_row - 1) + ',', end = '', flush = True)
			processes = []
			for row in range(start_row, stop_row):
				processes.append(subprocess.Popen(['python3', 'Modules/Scripts/HMM_row.py', self.videoObj.localTempDir + str(row) + '.npy']))
			for p in processes:
				p.communicate()
		print()
		all_data = []
		# Concatenate all data together
		for row in range(self.videoObj.height):
			all_data.append(np.load(self.videoObj.localTempDir + str(row) + '.hmm.npy'))
		out_data = np.concatenate(all_data, axis = 0)

		# Save npy and txt files for future use
		np.save(self.videoObj.localHMMFile + '.npy', out_data)
		with open(self.videoObj.localHMMFile + '.txt', 'w') as f:
			print('Width: ' + str(self.videoObj.width), file = f)
			print('Height: ' + str(self.videoObj.height), file = f)
			print('Frames: ' + str(int(self.HMMsecs*self.videoObj.framerate)), file = f)
			print('Resolution: ' + str(int(self.videoObj.framerate)), file = f)

		# Delete temp data

	def _createClusters(self):
		print('Creating clusters from HMM transitions,,Time: ' + str(datetime.datetime.now())) 

		# Load in HMM data
		hmmObj = HA(self.videoObj.localHMMFile)

		# Convert into coords object and save it
		coords = hmmObj.retDBScanMatrix(self.projFileManager.minMagnitude)
		np.save(self.videoObj.localRawCoordsFile, coords)
		
		# Run data in batches to avoid RAM override
		sortData = coords[coords[:,0].argsort()][:,0:3] #sort data by time for batch processing, throwing out 4th column (magnitude)
		numBatches = int(sortData[-1,0]/self.projFileManager.delta/3600) + 1 #delta is number of hours to batch together. Can be fraction.

		sortData[:,0] = sortData[:,0]*self.projFileManager.timeScale #scale time so that time distances between transitions are comparable to spatial differences
		labels = np.zeros(shape = (sortData.shape[0],1), dtype = sortData.dtype) # Initialize labels

		#Calculate clusters in batches to avoid RAM overuse
		curr_label = 0 #Labels for each batch start from zero - need to offset these 
		print(str(numBatches) + ' total batches. On batch: ', end = '', flush = True)
		for i in range(numBatches):
			print(str(i) + ',', end = '', flush = True)

			min_time, max_time = i*self.projFileManager.delta*self.projFileManager.timeScale*3600, (i+1)*self.projFileManager.delta*self.projFileManager.timeScale*3600 # Have to deal with rescaling of time. 3600 = # seconds in an hour
			hour_range = np.where((sortData[:,0] > min_time) & (sortData[:,0] <= max_time))
			min_index, max_index = hour_range[0][0], hour_range[0][-1] + 1
			X = NearestNeighbors(radius=self.projFileManager.treeR, metric='minkowski', p=2, algorithm='kd_tree',leaf_size=self.projFileManager.leafNum,n_jobs=24).fit(sortData[min_index:max_index])
			dist = X.radius_neighbors_graph(sortData[min_index:max_index], self.projFileManager.neighborR, 'distance')
			sub_label = DBSCAN(eps=self.projFileManager.eps, min_samples=self.projFileManager.minPts, metric='precomputed', n_jobs=self.workers).fit_predict(dist)
			new_labels = int(sub_label.max()) + 1
			sub_label[sub_label != -1] += curr_label
			labels[min_index:max_index,0] = sub_label
			curr_label += new_labels

		# Concatenate and save information
		sortData[:,0] = sortData[:,0]/self.projFileManager.timeScale
		labeledCoords = np.concatenate((sortData, labels), axis = 1).astype('int64')
		np.save(self.videoObj.localLabeledCoordsFile, labeledCoords)
		print('Concatenating and summarizing clusters,,Time: ' + str(datetime.datetime.now())) 

		df = pd.DataFrame(labeledCoords, columns=['T','X','Y','LID'])
		clusterData = df.groupby('LID').apply(lambda x: pd.Series({
			'projectID': self.lp.projectID,
			'videoID': self.videoObj.baseName,
			'N': x['T'].count(),
			't': int(x['T'].mean()),
			'X': int(x['X'].mean()),
			'Y': int(x['Y'].mean()),
			't_span': int(x['T'].max() - x['T'].min()),
			'X_span': int(x['X'].max() - x['X'].min()),
			'Y_span': int(x['Y'].max() - x['Y'].min()),
			'ManualAnnotation': 'No',
			'ManualLabel': '',
			'ClipCreated': 'No',
			'DepthChange': np.nan,
		})
		)
		clusterData['TimeStamp'] = clusterData.apply(lambda row: (self.videoObj.startTime + datetime.timedelta(seconds = int(row.t))), axis=1)
		clusterData['ClipName'] = clusterData.apply(lambda row: '__'.join([str(x) for x in [self.lp.projectID, self.videoObj.baseName,row.name,row.N,row.t,row.X,row.Y]]), axis = 1)
		# Identify clusters to make clips for
		#self._print('Identifying clusters to make clips for', log = False)
		delta_xy = self.projFileManager.delta_xy
		delta_t = self.projFileManager.delta_t
		smallClips, clipsCreated = 0,0 # keep track of clips with small number of pixel changes
		for row in clusterData.sample(n = clusterData.shape[0]).itertuples(): # Randomly go through the dataframe
			LID, N, t, x, y, time = row.Index, row.N, row.t, row.X, row.Y, row.TimeStamp
			if x - delta_xy < 0 or x + delta_xy >= self.videoObj.height or y - delta_xy < 0 or y + delta_xy >= self.videoObj.width:
				continue
			# Check temporal compatability (part a):
			elif self.videoObj.framerate*t - delta_t < 0 or LID == -1:
				continue
			# Check temporal compatability (part b):
			elif time < self.lightsOnTime or time > self.lightsOffTime:
				continue
			else:
				clusterData.loc[clusterData.index == LID,'ClipCreated'] = 'Yes'
				if N < self.projFileManager.smallLimit:
					if smallClips > self.projFileManager.nManualLabelClips/20:
						continue
					smallClips += 1
				if clipsCreated < self.projFileManager.nManualLabelClips:
					clusterData.loc[clusterData.index == LID,'ManualAnnotation'] = 'Yes'
					clipsCreated += 1

		clusterData.to_csv(self.videoObj.localLabeledClustersFile, sep = ',')
		self.clusterData = clusterData

	def _createAnnotationFiles(self):
		print('Creating small video clips for classification and manual labeling,,Time: ' + str(datetime.datetime.now())) 

		# Clip creation is super slow so we do it in parallel
		self.clusterData = pd.read_csv(self.videoObj.localLabeledClustersFile, sep = ',', index_col = 'LID')
		self.clusterData['ClipName'] = self.clusterData.apply(lambda row: '__'.join([str(x) for x in [self.lp.projectID, self.videoObj.baseName,row.name,row.N,row.t,row.X,row.Y]]), axis = 1)

		hmmObj = HA(self.videoObj.localHMMFile)

		# Create clips for each cluster
		processes = []
		for row in self.clusterData[self.clusterData.ClipCreated == 'Yes'].itertuples():
			LID, N, t, x, y = [str(x) for x in [row.Index, row.N, row.t, row.X, row.Y]]
			outName = self.projFileManager.localAllClipsDir + '__'.join([self.lp.projectID, self.videoObj.baseName,LID,N,t,x,y]) + '.mp4'
			command = ['python3', 'Modules/Scripts/createClip.py', self.videofile, 
						outName, str(self.projFileManager.delta_xy), str(self.projFileManager.delta_t), str(self.videoObj.framerate)]
			processes.append(subprocess.Popen(command))
			if len(processes) == self.workers:
				for p in processes:
					p.communicate()
				processes = []

		# Create video clips for manual labeling - this includes HMM data
		cap = cv2.VideoCapture(self.videofile)
		delta_xy = self.projFileManager.delta_xy
		delta_t = self.projFileManager.delta_t
		labeledCoords = np.load(self.videoObj.localLabeledCoordsFile)
		for row in self.clusterData[self.clusterData.ManualAnnotation == 'Yes'].itertuples():
			LID, N, t, x, y, clipname = row.Index, row.N, row.t, row.X, row.Y, row.ClipName
			
			outName_ml = self.projFileManager.localManualLabelClipsDir + clipname + '_ManualLabel.mp4'
			outName_in = self.projFileManager.localAllClipsDir + clipname + '.mp4'
			outName_out = self.projFileManager.localManualLabelClipsDir + clipname + '.mp4'

			outAllHMM = cv2.VideoWriter(outName_ml, cv2.VideoWriter_fourcc(*"mp4v"), self.videoObj.framerate, (4*delta_xy, 2*delta_xy))
			cap.set(cv2.CAP_PROP_POS_FRAMES, int(self.videoObj.framerate*(t) - delta_t))
			HMMChanges = hmmObj.retDifference(self.videoObj.framerate*(t) - delta_t, self.videoObj.framerate*(t) + delta_t)
			clusteredPoints = labeledCoords[labeledCoords[:,3] == LID][:,1:3]

			for i in range(delta_t*2):
				ret, frame = cap.read()
				frame2 = frame.copy()
				frame[HMMChanges != 0] = [300,125,125]
				for coord in clusteredPoints: # This can probably be improved to speed up clip generation (get rid of the python loop)
					frame[coord[0], coord[1]] = [125,125,300]
				outAllHMM.write(np.concatenate((frame2[x-delta_xy:x+delta_xy, y-delta_xy:y+delta_xy], frame[x-delta_xy:x+delta_xy, y-delta_xy:y+delta_xy]), axis = 1))

			
			outAllHMM.release()

			subprocess.call(['cp', outName_in, outName_out])
			assert(os.path.exists(outName_out))
		cap.release()


		# Create frames for manual labeling
		cap = cv2.VideoCapture(self.videofile)

		first_frame = 0
		if self.videoObj.startTime < self.lightsOnTime:
			first_frame = int((self.lightsOnTime - self.videoObj.startTime).total_seconds()*self.videoObj.framerate)
		else:
			first_frame = 0
		last_frame = first_frame + int((self.lightsOffTime - self.lightsOnTime).total_seconds()*self.videoObj.framerate)
		
		last_frame = min(self.frames, last_frame)

		for i in range(self.projFileManager.nManualLabelFrames):
			frameIndex = random.randint(first_frame, last_frame)
			cap.set(cv2.CAP_PROP_POS_FRAMES, frameIndex)
			ret, frame = cap.read()
			cv2.imwrite(self.projFileManager.localManualLabelFramesDir + self.lp.projectID + '_' + self.videoObj.baseName + '_' + str(frameIndex) + '.jpg', frame)     # save frame as JPEG file      

 


