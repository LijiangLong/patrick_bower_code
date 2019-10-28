from Modules.FileManager import FileManager as FM
from Modules.CropPreparer import CropPreparer as CP
from Modules.DepthPreparer import DepthPreparer as DP
from Modules.DepthAnalyzer import DepthAnalyzer as DA
from Modules.FigureMaker import FigureMaker as FD
import os

fm_obj = FM('MC22_2')

#projDownloader.preparePrepAnalysis()
#projDownloader.prepareDepthAnalysis()
"""
master_directory = os.getenv('HOME') + '/Dropbox (GaTech)/McGrath/Apps/CichlidPiData/'
for projectID in os.listdir(master_directory):
	projectID = 'MC22_2'
	try:
		sdirs = os.listdir(master_directory + projectID)
	except NotADirectoryError:
		continue

	if 'Frames.tar' in sdirs:
		#addPrepFiles(projectID, master_directory)
		fm_obj = FM(projectID)
		fm_obj.prepareDepthAnalysis()
		dpt_obj = DP(fm_obj)
		dpt_obj.createSmoothedArray()
		fm_obj.backupDepthAnalysis()
		fm_obj.localDelete()
	break
"""
#fm_obj.prepareCropAnalysis()
#cp_obj = CP(fm_obj)
#cp_obj.prepData()
#fm_obj.backupCropAnalysis()
#fm_obj.localDelete()

fm_obj.prepareFigureAnalysis()
da_obj = FD(fm_obj)
da_obj.createDepthFigures()
fm_obj.backupFigureAnalysis()

#da_obj.createFigures()
#fm_obj.backupFigureAnalysis()
#fm_obj.localDelete()