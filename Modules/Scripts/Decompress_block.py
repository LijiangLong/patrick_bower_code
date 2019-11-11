import argparse, pdb, cv2
cv2.setNumThreads(1) 
import numpy as np

parser = argparse.ArgumentParser(description='This command helps to decompress mp4 file')
parser.add_argument('Videofile', type = str, help = 'The name of the mp4 file that will be decompressed')
parser.add_argument('Framerate', type = int, help = 'The framerate of the video')
parser.add_argument('FirstTime', type = int, help = 'The first time to grab (seconds)')
parser.add_argument('LastTime', type = int, help = 'The last time to grab (seconds)')
parser.add_argument('OutFile', type = str, help = 'The outputfile to create')

args = parser.parse_args()

cap = cv2.VideoCapture(args.Videofile)
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

ad = np.empty(shape = (height, width, args.LastTime - args.FirstTime), dtype = 'uint8')

count = 0
for i in range(args.FirstTime, args.LastTime):
	cap.set(cv2.CAP_PROP_POS_FRAMES, int(i*args.Framerate))
	ret, frame = cap.read()
	if not ret:
		raise Exception('Cant read frame')
	ad[:,:,count] =  0.2125 * frame[:,:,2] + 0.7154 * frame[:,:,1] + 0.0721 * frame[:,:,0] #opencv does bgr instead of rgb
	count += 1
cap.release()

np.save(args.OutFile, ad)
assert(count == ad.shape[2])
