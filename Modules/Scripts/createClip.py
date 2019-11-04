import argparse, pdb, cv2

parser = argparse.ArgumentParser(description='This command runs HMM analysis on a single row of data.')
parser.add_argument('Videofile', type = str, help = 'The name of the video file that will be used to create clips')
parser.add_argument('Outfile', type = str, help = 'The name of the video file that will be created')
parser.add_argument('Delta_xy', type = int, help = 'x and y bounds of the clip')
parser.add_argument('Delta_t', type = int, help = 'the length f the clip')
parser.add_argument('Framerate', type = float, help = 'The framerate of the video')

args = parser.parse_args()

#print(args.Outfile)
#print(args.Outfile.split('/')[-1].replace('.mp4','').split('__'))
projectID, videoID, LID, N, t, x, y = args.Outfile.split('/')[-1].replace('.mp4','').split('__')
t,x,y = int(t), int(x), int(y)

cap = cv2.VideoCapture(args.Videofile)
	
outAll = cv2.VideoWriter(args.Outfile, cv2.VideoWriter_fourcc(*"mp4v"), args.Framerate, (2*args.Delta_xy, 2*args.Delta_xy))

cap.set(cv2.CAP_PROP_POS_FRAMES, int(args.Framerate*(t) - args.Delta_t))
for i in range(args.Delta_t*2):
	ret, frame = cap.read()
	if ret:
		outAll.write(frame[x-args.Delta_xy:x+args.Delta_xy, y-args.Delta_xy:y+args.Delta_xy])
	else:
		print('VideoError: BadFrame for ' + LID)
outAll.release()
