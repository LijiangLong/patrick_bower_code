import torch.utils.data as data
import cv2, os, pdb, random
import torchvision.models.video
from torchvision import transforms
import numpy as np
import torch



class VideoLoader(data.Dataset):
	def __init__(self,directory, train_flag, output_shape):
		self.directory = directory # Directory containing the videos in this format: label/___.mp4
		self.train_flag = train_flag # For training, videos are randomly cropped
		self.output_shape = output_shape # (t, w, h)

		self.labels = {} # will hold the labels for each mp4
		self.videofiles = [] # Holds the location of all the video files

		# Add videofiles and 
		for label in [x for x in os.listdir(directory) if os.path.isdir(directory + x)]:
			for videofile in [x for x in os.listdir(directory + label) if '.mp4' in x]:
				self.labels[directory + label + '/' + videofile] = label
				self.videofiles.append(directory + label + '/' + videofile)

		# Get size of mp4
		cap = cv2.VideoCapture(self.videofiles[0])
		self.frames = 0
		ret,frame = cap.read()
		self.width, self.height = frame.shape[0:2]
		while ret:
			self.frames += 1
			ret,frame = cap.read()

		self.transforms = transforms.ToTensor()

		
	def __getitem__(self, index):
		cap = cv2.VideoCapture(self.videofiles[index])
		data = np.zeros(shape = (3,self.frames, self.width, self.height))    	#(c,t,w,h)

		for i in range(self.frames):
			ret, frame = cap.read()
			data[0,i] = frame[:,:,0]
			data[1,i] = frame[:,:,1]
			data[2,i] = frame[:,:,2]
			
		means = data[:,0].mean(axis = (1,2))
		stds = data[:,0].std(axis = (1,2))
		
		t_cut = self.frames - self.output_shape[0] # 30
		x_cut = self.width - self.output_shape[1] # 88
		y_cut = self.height - self.output_shape[2] # 88

		if self.train_flag:
			new_t = random.randint(0,t_cut)
			new_x = random.randint(int(x_cut/4), int(3*x_cut/4))
			new_y = random.randint(int(y_cut/4), int(3*y_cut/4))
		else:
			new_t = int(t_cut/2)
			new_x = int(x_cut/2)
			new_y = int(y_cut/2)

		cropped_data = data[:,new_t:new_t + self.output_shape[0], new_x: new_x + self.output_shape[1], new_y: new_y + self.output_shape[2]]

		if random.randint(0,2) == 0 and self.train_flag:
			cropped_data = np.flip(cropped_data, axis = 1).copy()

		for c in range(3):
			cropped_data[c] = (cropped_data[c] - means[c])/stds[c]

		return (torch.from_numpy(cropped_data), self.labels[self.videofiles[index]], self.videofiles[index].split('/')[-1])

videoLoader = VideoLoader('Clips/', True, (90,112,112))
a = videoLoader[0]

model = torchvision.models.video.r3d_18(pretrained=True, progress=True)
model(a[0].unsqueeze(0).float())

