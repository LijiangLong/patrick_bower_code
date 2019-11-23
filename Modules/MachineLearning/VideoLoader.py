import torch.utils.data as data
import cv2
import torchvision.models.video

torchvision.models.video.r3d_18(pretrained=False, progress=True, **kwargs)

class VideoLoader(data.Dataset):
	def __init__(self,width,height,frames,train_flag):
        self.data, self.class_names = make_dataset(
            root_path, annotation_path, subset, n_samples_for_each_video,
            sample_duration)

        self.spatial_transforms = spatial_transforms
        self.temporal_transform = temporal_transform
        self.target_transform = target_transform
        self.loader = get_loader()
        self.annotationDict = annotationDict

    def __getitem__(self, index):
    	cap = cv2.VideoCapture(self.videofiles[i])
    	data = np.zeros(shape = (self.input_shape))    	#(c,l,w,h)

    	for i in range(self.input_shape[2]):
	    	ret, frame = cap.read()
	    	data[0,i] = frame[:,:,0]
	    	data[1,i] = frame[:,:,1]
	    	data[2,i] = frame[:,:,2]
	    	
	    means = data[:,0].mean()

	    x_crop = 88 44 -> 156 0 -> 22 -> 66
	    y_crop = 88
	    t_crop =  15 - 105 0-30

	    200, 200, 120
	    112, 112, 90

	    t_crop = 40 200 112 112 
	    x_crop = 50
	    y_crop = 50

	    # If training data, randomly crop spatial and temporal direction