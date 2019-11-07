from Modules.FileManager import FileManager as FM

import matplotlib.pyplot as plt
import matplotlib, datetime, cv2, pdb, os
from Modules.roipoly import roipoly
import numpy as np



class CropPreparer:

	def __init__(self, projectID):
		self.projectID = projectID
		self.fileManager = FM()
		self.anFileManager = self.fileManager.retAnFileManager()
		self.projFileManager = self.fileManager.retProjFileManager(projectID)
		self.__version__ = '1.0.0'

	def prepData(self):
		self.projFileManager.prepareCropAnalysis()
		self._identifyTray()
		self._cropVideo()
		self._registerDepthCamera()
		self._summarizePrep()
		self._createAnalysisUpdate()
		self.projFileManager.backupCropAnalysis()
		self.projFileManager.localDelete()
		self.anFileManager.deleteAnalysisDir()

	def _identifyTray(self, thresh = 10):

		firstFrame = np.load(self.projFileManager.localFirstFrame)
		lastFrame = np.load(self.projFileManager.localLastFrame)
		depthRGB = cv2.imread(self.projFileManager.localDepthRGB)

		# Create color image of depth change
		cmap = plt.get_cmap('jet')
		cmap.set_bad(color = 'black')
		final_image = cmap(plt.Normalize(-10,10)(lastFrame - firstFrame))

		# Loop until an acceptable box is created
		while True:
			# Query user to identify regions of the tray that are good
			cv2.imshow('Identify the parts of the frame that include tray to analyze', final_image)
			tray_r = cv2.selectROI('Identify the parts of the frame that include tray to analyze', final_image, fromCenter = False)
			tray_r = tuple([int(x) for x in tray_r]) # sometimes a float is returned
			self.tray_r = [tray_r[1],tray_r[0],tray_r[1] + tray_r[3], tray_r[0] + tray_r[2]] # (x0,y0,xf,yf)
		
			# if bounding box is close to the edge just set it as the edge
			if self.tray_r[0] < thresh: 
				self.tray_r[0] = 0
			if self.tray_r[1] < thresh: 
				self.tray_r[1] = 0
			if final_image.shape[0] - self.tray_r[2]  < thresh: 
				self.tray_r[2] = final_image.shape[0]
			if final_image.shape[1] - self.tray_r[3]  < thresh:  
				self.tray_r[3] = final_image.shape[1]

			# Destroy windows (running it 3 times helps for some reason)
			for i in range(3):
				cv2.destroyAllWindows()
				cv2.waitKey(1)

			# Create figure for user to see the crop
			fig = plt.figure(figsize=(9, 9))
			ax1 = fig.add_subplot(2,2,1)       
			ax2 = fig.add_subplot(2,2,2)
			ax3 = fig.add_subplot(2,2,3)
			ax4 = fig.add_subplot(2,2,4)
			ax1.imshow(depthRGB)
			ax1.add_patch(matplotlib.patches.Rectangle((self.tray_r[1],self.tray_r[0]), self.tray_r[3] - self.tray_r[1], self.tray_r[2] - self.tray_r[0], color="orange", fill = False, lw = 3.0))
			ax1.set_title("Depth RGB")
			ax2.imshow(lastFrame - firstFrame, cmap = cmap)
			ax2.add_patch(matplotlib.patches.Rectangle((self.tray_r[1],self.tray_r[0]), self.tray_r[3] - self.tray_r[1], self.tray_r[2] - self.tray_r[0], color="orange", fill = False, lw = 3.0))
			ax2.set_title("Depth change over whole trial")
			ax3.imshow(firstFrame, cmap = cmap)
			ax3.add_patch(matplotlib.patches.Rectangle((self.tray_r[1],self.tray_r[0]), self.tray_r[3] - self.tray_r[1], self.tray_r[2] - self.tray_r[0], color="orange", fill = False, lw = 3.0))
			ax3.set_title("Depth at early time point")
			ax4.imshow(lastFrame, cmap = cmap)
			ax4.add_patch(matplotlib.patches.Rectangle((self.tray_r[1],self.tray_r[0]), self.tray_r[3] - self.tray_r[1], self.tray_r[2] - self.tray_r[0], color="orange", fill = False, lw = 3.0))
			ax4.set_title("Depth at late time point")
			fig.canvas.set_window_title('Close window and type q in terminal if this is acceptable')
			plt.show()

			userInput = input('Type q if this is acceptable: ')
			if userInput == 'q':
				break

		# Save and back up tray file
		with open(self.projFileManager.localTrayFile, 'w') as f:
			print(','.join([str(x) for x in self.tray_r]), file = f)

	def _cropVideo(self):
		im1 =  cv2.imread(self.projFileManager.localPiRGB)
		im1_gray = cv2.cvtColor(im1,cv2.COLOR_BGR2GRAY)

		while True:
			im1 =  cv2.imread(self.projFileManager.localPiRGB)
			im1_gray = cv2.cvtColor(im1,cv2.COLOR_BGR2GRAY)

			fig = plt.figure(figsize=(9, 12))
		
			plt.imshow(im1_gray, cmap='gray')

			plt.title('Select four points in this object (Double-click on the fourth point)')
			ROI1 = roipoly(roicolor='r')
			plt.show()

			if len(ROI1.allxpoints) != 4:
				print('Wrong length, ROI1 = ' + str(len(ROI1.allxpoints)))
				continue

			self.videoPoints = np.array([[ROI1.allxpoints[0], ROI1.allypoints[0]], [ROI1.allxpoints[1], ROI1.allypoints[1]], [ROI1.allxpoints[2], ROI1.allypoints[2]], [ROI1.allxpoints[3], ROI1.allypoints[3]]])

			fig = plt.figure(figsize=(9, 12))
			self.videoCrop = ROI1.getMask(im1_gray)
			im1_gray[~self.videoCrop] = 0
			plt.imshow(im1_gray, cmap='gray')
			plt.title('Close window and type q in terminal if this is acceptable')
			#fig.savefig(self.localMasterDirectory + self.videoCropFig)
			plt.show()

			userInput = input('Type q if this is acceptable: ')
			if userInput == 'q':
				#self.videoCrop = ROI1.getMask(im1_gray)
				break

		np.save(self.projFileManager.localVideoCropFile, self.videoCrop)
		np.save(self.projFileManager.localVideoPointsFile, self.videoPoints)

	def _registerDepthCamera(self):

		# Unable to load it from existing file, either because it doesn't exist or the rewrite flag was set
		print('Registering RGB and Depth data ')
		# Find first videofile during the day

		im1 = cv2.imread(self.projFileManager.localDepthRGB)
		im2 = cv2.imread(self.projFileManager.localPiRGB)
		im1_gray = cv2.cvtColor(im1,cv2.COLOR_BGR2GRAY)
		im2_gray = cv2.cvtColor(im2,cv2.COLOR_BGR2GRAY)

		while True:
			fig = plt.figure(figsize=(18, 12))
			ax1 = fig.add_subplot(1,2,1)       
			ax2 = fig.add_subplot(1,2,2)
		
			ax1.imshow(im1_gray, cmap='gray')
			ax2.imshow(im2_gray, cmap='gray')

			ax1.set_title('Select four points in this object (Double-click on the fourth point)')
			ROI1 = roipoly(roicolor='r')
			plt.show()
			fig = plt.figure(figsize=(18, 12))
			ax1 = fig.add_subplot(1,2,1)       
			ax2 = fig.add_subplot(1,2,2)
  
			ax1.imshow(im1_gray, cmap='gray')
			ROI1.displayROI(ax = ax1)
			ax2.imshow(im2_gray, cmap='gray')

			ax2.set_title('Select four points in this object (Double-click on the fourth point)')
			ROI2 = roipoly(roicolor='b')
			plt.show()


			if len(ROI1.allxpoints) != 4 or len(ROI2.allxpoints) != 4:
				print('Wrong length, ROI1 = ' + str(len(ROI1.allxpoints)) + ', ROI2 = ' + str(len(ROI2.allxpoints)))
				continue
		
			ref_points =[[ROI1.allxpoints[0], ROI1.allypoints[0]], [ROI1.allxpoints[1], ROI1.allypoints[1]], [ROI1.allxpoints[2], ROI1.allypoints[2]], [ROI1.allxpoints[3], ROI1.allypoints[3]]]
			new_points =[[ROI2.allxpoints[0], ROI2.allypoints[0]], [ROI2.allxpoints[1], ROI2.allypoints[1]], [ROI2.allxpoints[2], ROI2.allypoints[2]], [ROI2.allxpoints[3], ROI2.allypoints[3]]]

		
			self.transM = cv2.getPerspectiveTransform(np.float32(new_points),np.float32(ref_points))
			newImage = cv2.warpPerspective(im2_gray, self.transM, (640, 480))

			fig = plt.figure(figsize=(18, 12))
			ax1 = fig.add_subplot(1,2,1)       
			ax2 = fig.add_subplot(1,2,2)
		
			ax1.imshow(im1_gray, cmap='gray')
			ax1.set_title("Depth RGB image")

			ax2.imshow(newImage, cmap='gray')
			ax2.set_title("Registered Pi RGB image")

			#fig.savefig(self.localMasterDirectory + self.transFig)
			fig.canvas.set_window_title('Close window and type q in terminal if this is acceptable')
			plt.show()

			userInput = input('Type q if this is acceptable: ')
			if userInput == 'q':
				break

		np.save(self.projFileManager.localTransMFile, self.transM)

	def _summarizePrep(self):
		firstFrame = np.load(self.projFileManager.localFirstFrame)
		lastFrame = np.load(self.projFileManager.localLastFrame)
		depthRGB = cv2.imread(self.projFileManager.localDepthRGB)
		#depthRGB = cv2.cvtColor(depthRGB,cv2.COLOR_BGR2GRAY)
		piRGB =  cv2.imread(self.projFileManager.localPiRGB)
		piRGB = cv2.cvtColor(piRGB,cv2.COLOR_BGR2GRAY)

		cmap = plt.get_cmap('jet')
		cmap.set_bad(color = 'black')

		fig = plt.figure(figsize=(12, 12))
		ax1 = fig.add_subplot(2,2,1)       
		ax2 = fig.add_subplot(2,2,2)
		ax3 = fig.add_subplot(2,2,3)
		ax4 = fig.add_subplot(2,2,4)

		ax1.imshow(depthRGB, cmap = 'gray')
		ax1.add_patch(matplotlib.patches.Rectangle((self.tray_r[1],self.tray_r[0]), self.tray_r[3] - self.tray_r[1], self.tray_r[2] - self.tray_r[0], color="orange", fill = False, lw = 3.0))
		ax1.set_title("Depth RGB image with depth crop")

		ax2.imshow(lastFrame - firstFrame, cmap = cmap)
		ax2.add_patch(matplotlib.patches.Rectangle((self.tray_r[1],self.tray_r[0]), self.tray_r[3] - self.tray_r[1], self.tray_r[2] - self.tray_r[0], color="orange", fill = False, lw = 3.0))
		ax2.set_title("Total trial depth change image with depth crop")
	
		piRGB[~self.videoCrop] = 0
		ax3.imshow(piRGB, cmap='gray')
		ax3.set_title("Pi RGB image with video crop")

		warpedPiRGB = cv2.warpPerspective(piRGB, self.transM, (640, 480))
		ax4.imshow(warpedPiRGB, cmap = 'gray')
		ax4.add_patch(matplotlib.patches.Rectangle((self.tray_r[1],self.tray_r[0]), self.tray_r[3] - self.tray_r[1], self.tray_r[2] - self.tray_r[0], color="orange", fill = False, lw = 3.0))
		ax4.set_title("Registered Pi RGB image with video and depth crop")

		fig.savefig(self.projFileManager.localPrepSummaryFigure, dpi=300)

		plt.show()

	def _createAnalysisUpdate(self):
		now = datetime.datetime.now()
		with open(self.anFileManager.localMasterDir + 'AnalysisUpdate_' + str(now) + '.csv', 'w') as f:
			print('ProjectID,Type,Version,Date', file = f)
			print(self.projectID + ',Prep,' + os.getenv('USER') + '_' + self.__version__ + ',' + str(now), file= f)
		self.anFileManager.uploadAnalysisUpdate('AnalysisUpdate_' + str(now) + '.csv')
