from Modules.FileManagers.FileManager import FileManager as FM
import subprocess, pdb

anFM_obj = FM().retAnFileManager()

labeledClipsDir = anFM_obj.prepareVideoAnnotation('10classLabels')
#labeledClipsDir = '/Users/pmcgrath7/Temp/CichlidAnalyzer/__AnnotatedData/LabeledVideos/10classLabels/LabeledClips/'
#pdb.set_trace()

#subprocess.run(['python3', 'Modules/MachineLearning/3D_resnet.py', '--data', labeledClipsDir])
