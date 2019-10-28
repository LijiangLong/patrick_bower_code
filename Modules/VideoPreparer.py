class VideoPreparer:
	# This class takes in directory information and a logfile containing depth information and performs the following:
	# 1. Identifies tray using manual input
	# 2. Interpolates and smooths depth data
	# 3. Automatically identifies bower location
	# 4. Analyze building, shape, and other pertinent info of the bower

	def __init__(self, fileManager, videoObj, videofile, workers):
		self.fileManager = fileManager
		self.videoObj = videoObj
		self.videofile = videofile
		self.workers = workers

	def _validateVideo(self, tol = 0.001, log = False):
        assert os.path.isfile(self.videofile)
        
        cap = cv2.VideoCapture(self.videofile)
        new_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        new_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        new_framerate = cap.get(cv2.CAP_PROP_FPS)
        new_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        predicted_frames = int((self.videoObj.endTime - self.videoObj.startTime).total_seconds()*self.videoObj.frame_rate)

        self._print('VideoValidation: Size: ' + str((new_height,new_width)) + ',,fps: ' + str(new_framerate) + ',,Frames: ' + str(new_frames) + ',,PredictedFrames: ' + str(predicted_frames), log = log)

        assert new_height == self.videoObj.height
        assert new_width == self.videoObj.width
        assert abs(new_framerate - self.videoObj.frame_rate) < tol*self.videoObj.frame_rate
        assert abs(predicted_frames - new_frames) < tol*predicted_frames

        self.frames = new_frames

        cap.release()

	def _decompressVideo(self, blocksize = 5*60):

		# Don't process videos when the lights are dimmed (>6pm)
		self.blocksize = blocksize

		maxTime = min(self.videoObj.endTime, self.videoObj.startTime.replace(hour = 18, minute = 0, second = 0, microsecond = 0)) # Lights dim at 6pm. 
        self.HMMsecs = (maxTime - self.videoObj.startTime).total_seconds() - 1

        totalBlocks = math.ceil(HMMsecs/(blocksize)) #Number of blocks that need to be analyzed for the full video
        pool = ThreadPool(self.workers) #Create pool of threads for parallel analysis of data

        for i in range(0, totalBlocks, self.workers):
            blocks = list(range(i, min(i + self.workers, blocks)))
            self._print('Minutes since start: ' + str((datetime.datetime.now() - start).seconds/60) + ', Processing blocks: ' + str(blocks[0]) + ' to ' +  str(blocks[-1]), log = False)
            results = pool.map(self._readBlock, blocks)
            print('Data read: ' + str((datetime.datetime.now() - start).seconds) + ' seconds')
            for row in range(self.videoObj.height):
                row_file = self.fileManager.localTempDir + str(row) + '.npy'
                out_data = np.concatenate([results[x][row] for x in range(len(results))], axis = 1)
                if os.path.isfile(row_file):
                    out_data = np.concatenate([np.load(row_file),out_data], axis = 1)
                np.save(row_file, out_data)
            print('Data wrote: ' + str((datetime.datetime.now() - start).seconds) + ' seconds', file = sys.stderr)
        pool.close() 
        pool.join() 

    def _readBlock(self, block):
        min_t = block*self.blocksize
        max_t = min((block+1)*self.blocksize, self.HMMsecs)
        ad = np.empty(shape = (self.videoObj.height, self.videoObj.width, max_t - min_t), dtype = 'uint8')
        
        cap = cv2.VideoCapture(self.videofile)
        for i in range(max_t - min_t):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int((i+min_t)*self.frame_rate))
            ret, frame = cap.read()
            if not ret:
                raise Exception('Cant read frame')
            ad[:,:,i] =  0.2125 * frame[:,:,2] + 0.7154 * frame[:,:,1] + 0.0721 * frame[:,:,0] #opencv does bgr instead of rgb
        cap.release()
        return ad 

    def _calculateHMMs(self):
    	totalBlocks = 

