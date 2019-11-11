import argparse, pdb, cv2
import numpy as np

parser = argparse.ArgumentParser(description='This command helps to decompress mp4 file')
parser.add_argument('Videofile', type = str, help = 'The name of the mp4 file that will be decompressed')
parser.add_argument('Framerate', type = int, help = 'The framerate of the video')
parser.add_argument('Firstframe', type = int, help = 'The first frame to grab')
parser.add_argument('Lastframe', type = int, help = 'The last frame to grab')
parser.add_argument('OutFile', type = str, help = 'The outputfile to create')

args = parser.parse_args()

cap = cv2.VideoCapture(args.Videofile)
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

ad = np.empty(shape = (height, width, int((args.Lastframe - args.Firstframe)/args.Framerate)), dtype = 'uint8')

count = 0
for i in range(args.Firstframe, args.Lastframe, args.Framerate):
	cap.set(cv2.CAP_PROP_POS_FRAMES, i)
	ret, frame = cap.read()
	if not ret:
		raise Exception('Cant read frame')
	ad[:,:,count] =  0.2125 * frame[:,:,2] + 0.7154 * frame[:,:,1] + 0.0721 * frame[:,:,0] #opencv does bgr instead of rgb
	count += 1
cap.release()

np.save(args.OutFile, ad)
assert(count == ad.shape[2])
