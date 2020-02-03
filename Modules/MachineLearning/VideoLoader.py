import os
from torchvision import transforms
from skvideo import io as vp
from torch.utils import data
import torch
import numpy as np
import random
from time import time
import pdb

#torchvision.models.video.r3d_18(pretrained=False, progress=True, **kwargs)

class VideoLoader(data.Dataset):

    def __init__(self, directory, datatype, output_shape):
        self.directory = directory # Directory containing the videos in this format: label/___.mp4
        self.datatype = datatype.lower() # For training, videos are randomly cropped
        self.output_shape = output_shape # (t, w, h)

        # Directionary and list to hold data
        self.labels = {} # will hold the labels for each mp4
        self.videofiles = [] # Holds the location of all the video files

        # Transform labels to numbers
        label_to_number_file = '/'.join(self.directory.split('/')[:-2])+'/tenClass_v1.txt'
        self.label_to_number = {}
        with open(label_to_number_file,'r') as input:
            for line in input:
                number,category_short,category_long = line.rstrip().split()
                self.label_to_number[category_short] = int(number)-1
        # get the means and standard deviation for the pixels
        means_file = '/'.join(self.directory.split('/')[:-2])+'/MeansAll_vp.csv'
        self.means = {}
        self.vars = {}
        with open(means_file,'r') as input:
            _ = input.readline()
            for line in input:
                Clip,MeanR,MeanG,MeanB,StdR,StdG,StdB = line.rstrip().split(',')
                self.means[Clip] = np.array([MeanR,MeanG,MeanB]).astype('float64')
                self.vars[Clip] = np.array([StdR, StdG, StdB]).astype('float64')

        # Add videofiles and labels
        for label in [x for x in os.listdir(directory) if os.path.isdir(directory+'/'+x)]:
            for videofile in [x for x in os.listdir(directory +'/'+ label) if '.mp4' in x]:
                self.labels[videofile] = label
                self.videofiles.append(directory +'/'+ label+'/'+videofile)
#         get the means and standard deviation for the pixels
#         means_file = '/'.join(self.directory.split('/')[:-2])+'/MeansAll_vp.csv'
#         with open(means_file,'w') as output:
#             output.write(','.join(['Clip','MeanR','MeanG','MeanB','StdR','StdG','StdB']))
#             output.write('\n')
#             for i in range(len(self.videofiles)):
#                 if i%100 == 0:
#                     print(i)
#                 video = vp.vread(self.videofiles[i])
#                 video = np.transpose(video, (3, 0, 1, 2))
#                 means = np.reshape(video, (video.shape[0], -1)).mean(axis=1)
#                 stds = np.reshape(video, (video.shape[0], -1)).std(axis=1)
#                 means_str = ','.join([str(i) for i in means])
#                 stds_str = ','.join([str(i) for i in stds])
#                 output.write(','.join([self.videofiles[i].split('/')[-1].split('.')[0],means_str,stds_str]))
#                 output.write('\n')






    def __getitem__(self, index):

        # Read in video
        video = vp.vread(self.videofiles[index]) #(t,w,h,c)
        video_name = self.videofiles[index].split('/')[-1].split('.')[0]
        video = np.transpose(video,(3,0,1,2)) #(c,t,w,h)
            
        # Each video is normalized by its mean and standard deviation to account for changes in lighting across the tank
        means = self.means[video_name]
        stds = self.vars[video_name]
        
        # The final video size is smaller than the original video
        t_cut = video.shape[1] - self.output_shape[0] # how many frames to cut out: 30
        x_cut = video.shape[2] - self.output_shape[1] # how many pixels to cut out: 88
        y_cut = video.shape[3] - self.output_shape[2] # how many pixels to cut out: 88
        # Determine start and end indices for each dimension depending on datatype
        if self.datatype == 'train':
            new_t = random.randint(0,t_cut)
            new_x = random.randint(int(x_cut/4), int(3*x_cut/4))
            new_y = random.randint(int(y_cut/4), int(3*y_cut/4))
        elif self.datatype == 'val':
            new_t = int(t_cut/2)
            new_x = int(x_cut/2)
            new_y = int(y_cut/2)

        # Crop the video
        cropped_video = video[:,new_t:new_t + self.output_shape[0], new_x: new_x + self.output_shape[1], new_y: new_y + self.output_shape[2]]
#         Flip the video if training
        if random.randint(0,2) == 0 and self.datatype == 'train':
            cropped_video = np.flip(cropped_video, axis = 1)
#         cropped_video = np.flip(cropped_video, axis=1)


        # Normalize each channel data
        temp = np.zeros(cropped_video.shape)
        for c in range(3):
            temp[c] = (cropped_video[c] - means[c])/stds[c]
        cropped_video = temp
        # Return tensor, label, and filename
        filename = self.videofiles[index].split('/')[-1]
        return (torch.from_numpy(cropped_video.copy()), torch.tensor(self.label_to_number[self.labels[filename]]), filename)

    def __len__(self):
        return len(self.videofiles)


# pdb.set_trace()
# trainset = VideoLoader('/data/home/llong35/Temp/CichlidAnalyzer/__AnnotatedData/LabeledVideos/10classLabels/LabeledClips/training', 'train', (90,112,112))
# trainset.__getitem__(0)
# for i in range(trainset.__len__()):
#     if i == 6125:
#         pdb.set_trace()
#
#     trainset.__getitem__(i)