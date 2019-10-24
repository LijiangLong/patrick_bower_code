from Modules.FileManager import FileManager as FM
from Modules.DataPreparor import DataPreparor as DP

#projDownloader = FM('MC22_2')

#projDownloader.preparePrepAnalysis()
#projDownloader.prepareDepthAnalysis()

dp_obj = DP('MC22_2')
dp_obj.prepData()
