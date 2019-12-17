import os
from torchvision import transforms
from skvideo import io as vp
from torch.utils import data

#torchvision.models.video.r3d_18(pretrained=False, progress=True, **kwargs)

class VideoLoader(data.Dataset):

	def __init__(self, directory, datatype, output_shape):
		self.directory = directory # Directory containing the videos in this format: label/___.mp4
		self.datatype = datatype.lower() # For training, videos are randomly cropped
		self.output_shape = output_shape # (t, w, h)

		# Directionary and list to hold data
		self.labels = {} # will hold the labels for each mp4
		self.videofiles = [] # Holds the location of all the video files

		# Add videofiles and 
		for label in [x for x in os.listdir(directory) if os.path.isdir(directory+'/'+x)]:
			for videofile in [x for x in os.listdir(directory +'/'+ label) if '.mp4' in x]:
				self.labels[videofile] = label
				self.videofiles.append(directory +'/'+ label+'/'+videofile)

	def __getitem__(self, index):

		# Read in video
		video = vp.vread(self.videofiles[index]) #(t,w,h,c)
		video = np.reshape(video, (video.shape[3], video.shape[0], video.shape[1], video.shape[2])) #(c,t,w,h)
			
		# Each video is normalized by its mean and standard deviation to account for changes in lighting across the tank
		means = video[:,0].mean() # r,g,b
		stds = video[:,0].std() # r,g,b
		
		# The final video size is smaller than the original video
		t_cut = video.shape[1] - self.output_shape[0] # how many frames to cut out: 30
		x_cut = video.shape[2] - self.output_shape[1] # how many pixels to cut out: 88
		y_cut = video.shape[3] - self.output_shape[2] # how many pixels to cut out: 88

		# Determine start and end indices for each dimension depending on datatype
		if self.self.datatype == 'train':
			new_t = random.randint(0,t_cut)
			new_x = random.randint(int(x_cut/4), int(3*x_cut/4))
			new_y = random.randint(int(y_cut/4), int(3*y_cut/4))
		elif self.self.datatype == 'val':
			new_t = int(t_cut/2)
			new_x = int(x_cut/2)
			new_y = int(y_cut/2)

		# Crop the video
		cropped_video = video[:,new_t:new_t + self.output_shape[0], new_x: new_x + self.output_shape[1], new_y: new_y + self.output_shape[2]]

		# Flip the video if training
		if random.randint(0,2) == 0 and self.dataset == 'train':
			cropped_video = np.flip(cropped_data, axis = 1)

		# Normalize each channel data
		for c in range(3):
			cropped_video[c] = (cropped_video[c] - means[c])/stds[c]

		# Return tensor, label, and filename
		return (transforms.ToTensor(cropped_data), self.labels[self.videofiles[i]], self.videofiles[i].split('/')[-1])

	def __len__(self):
		return len(self.videofiles)



