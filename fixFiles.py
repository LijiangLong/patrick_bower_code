import os, subprocess,pdb
from Modules.FileManager import FileManager as FM
from Modules.LogParser import LogParser as LP

def addPrepFiles(projectID, master_directory):

	sdirs = os.listdir(master_directory + projectID)

	if 'PrepFiles' not in sdirs:
		if 'Frames' in sdirs:
			print('Adding prep files for: ' + projectID)
			try:
				logObj = LP(master_directory + projectID + '/Logfile.txt')
			except UnboundLocalError:
				print('Cant read logfile for: ' + projectID)
				return False
			try:
				subprocess.run(['mkdir', master_directory + projectID + '/PrepFiles'])
				subprocess.run(['cp', master_directory + projectID + '/' + logObj.frames[0].npy_file, master_directory + projectID + '/PrepFiles/FirstDepth.npy'])
				subprocess.run(['cp', master_directory + projectID + '/' + logObj.frames[-1].npy_file, master_directory + projectID + '/PrepFiles/LastDepth.npy'])
				subprocess.run(['cp', master_directory + projectID + '/' + logObj.movies[0].pic_file, master_directory + projectID + '/PrepFiles/PiCameraRGB.jpg'])
			
				depthObj = [x for x in logObj.frames if x.time > logObj.movies[0].time][0]
				subprocess.run(['cp', master_directory + projectID + '/' + depthObj.pic_file, master_directory + projectID + '/PrepFiles/DepthRGB.jpg'])
			except:
				print('Error fixing: ' + projectID)
				subprocess.run(['rm', '-rf', master_directory + projectID + '/PrepFiles'])
			return True
	return False

def tarFrameDir(projectID, master_directory):
	sdirs = os.listdir(master_directory + projectID)

	if 'Frames.tar' not in sdirs:
		if 'Frames' in sdirs:
			print('Tarring frame directory for: ' + projectID)
			master_cloud_directory = 'cichlidVideo:McGrath/Apps/CichlidPiData/' + projectID + '/'
			master_local_directory = os.getenv('HOME') + '/Temp/FileFixer/' + projectID + '/'
			if not os.path.exists(master_local_directory):
				os.makedirs(master_local_directory)

			subprocess.run(['rclone', 'copy', master_cloud_directory + 'Frames', master_local_directory + 'Frames'])
			output = subprocess.run(['tar', '-cvf', master_local_directory + 'Frames.tar', '-C', master_local_directory, 'Frames'], capture_output = True)
			subprocess.run(['rclone', 'copy', master_local_directory + 'Frames.tar', master_cloud_directory])

			subprocess.run(['rm','-rf', master_local_directory])

			#subprocess.run(['rclone', 'purge', master_cloud_directory + 'Frames'])

			return True
	return False

def remOldDirs(projectID, master_directory):
	sdirs = os.listdir(master_directory + projectID)
	old_dirs = ['SubAnalysis', ]
	for od in ['SubAnalysis', 'Output', 'DepthAnalysis']:
		if od in sdirs:
			master_cloud_directory = 'cichlidVideo:McGrath/Apps/CichlidPiData/' + projectID + '/'
			subprocess.run(['rclone', 'purge', master_cloud_directory + 'od'])

def converth264s(projectID, master_directory):
	sdirs = os.listdir(master_directory + projectID)
	if 'Videos' in sdirs:
		movies = [x for x in os.listdir(master_directory + projectID + '/' + 'Videos') if '.h264' in x]
		for i, movie in enumerate(movies):
			if movie.replace('.h264', '.mp4') not in movies:
				try:
					logObj = LP(master_directory + projectID + '/Logfile.txt')
				except UnboundLocalError:
					print('Cant read logfile for: ' + projectID)
					return False
				master_cloud_directory = 'cichlidVideo:McGrath/Apps/CichlidPiData/' + projectID + '/Videos/'
				master_local_directory = os.getenv('HOME') + '/Temp/FileFixer/' + projectID + '/'
				if not os.path.exists(master_local_directory):
					os.makedirs(master_local_directory)

				command = ['rclone', 'copy', master_cloud_directory + movie, master_local_directory]
				output = subprocess.run(command, capture_output = True)

				command = ['ffmpeg', '-r', str(logObj.movies[i].framerate), '-i', master_local_directory + movie, '-c:v', 'copy', '-r', str(logObj.movies[i].framerate), master_local_directory + movie.replace('.h264', '.mp4')]
				output = subprocess.run(command, capture_output = True)
		
				# Ensure the conversion went ok. 

				assert os.stat(master_local_directory + movie.replace('.h264','.mp4')).st_size >= os.stat(master_local_directory + movie).st_size
				command = ['rclone', 'copy', master_local_directory + movie.replace('.h264', '.mp4'), master_cloud_directory]
				output = subprocess.run(command, capture_output = True)


def reorganizeClipFiles(master_directory):

	clipDir = master_directory + '__AnnotatedData/LabeledVideos/10ClassLabels/Clips/'
	for clip in os.listdir(clipDir):
		if clip[0] == '.' or '.mp4' not in clip:
			continue

		projectID = clip.split('__')[0]
		outdir = clipDir + projectID + '/'

		if not os.path.exists(outdir):
			os.makedirs(outdir)

		oldfile = clipDir + clip

		subprocess.run(['mv', oldfile, outdir])
		
	for projectID in os.listdir(clipDir):
		outdir = clipDir + projectID + '/'
		if 'mp4' in projectID:
			continue
		subprocess.run(['tar', '-cvf', outdir[:-1] + '.tar', '-C', clipDir, projectID])

master_directory = os.getenv('HOME') + '/Dropbox (GaTech)/McGrath/Apps/CichlidPiData/'
reorganizeClipFiles(master_directory)

"""for projectID in os.listdir(master_directory):
	try:
		sdirs = os.listdir(master_directory + projectID)
	except NotADirectoryError:
		continue
	projectID = '_newtray_Test'
	#addPrepFiles(projectID, master_directory)
	converth264s(projectID, master_directory)
	break"""