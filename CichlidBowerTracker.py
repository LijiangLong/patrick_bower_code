import argparse, os, pdb, sys
from Modules.DataPreparers.AnalysisPreparer import AnalysisPreparer as AP
from Modules.DataPreparers.ProjectPreparer import ProjectPreparer as PP

def parseProjects(args, analysisType):

	masObj = MAS()
	masObj.downloadAnalysisDir()

	if args.ProjectIDs[0].upper() != 'ALL' or len(args.ProjectIDs) != 1:
		allProjects = masObj.retProjects() #Make sure requested projects actually exist

		projects = set(args.ProjectIDs) # Remove any duplicates
		badProjects = projects.copy()
		for project in projects:
			if project not in allProjects:
				continue
			badProjects.remove(project) # project is good, so remove it

		if len(badProjects) != 0: # if all projects haven't been removed, then there are bad data
			print(str(badProjects) + ' are not valid projectIDs. Valid options are:')
			print(str(allProjects))
			raise KeyError
	else:
		projects = masObj.retProjects(unRun = analysisType)
		if args.Number is not None:
			projects = projects[:min(len(projects), args.Number)]
	masObj.deleteAnalysisDir()
	return projects

def updateAnalysisSummary():

	masObj = MAS()
	masObj.downloadAnalysisDir()
	masObj.addNewProjects()
	masObj.mergeUpdates()
	masObj.uploadAnalysisDir()
	masObj.deleteAnalysisDir()


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(help='Available Commands', dest='command')

trackerParser = subparsers.add_parser('CollectData', help='This command runs on Raspberry Pis to collect depth and RGB data')

summarizeParser = subparsers.add_parser('UpdateAnalysisSummary', help='This command identifies any new projects that can be analyzed and merges any updates that are new')

prepParser = subparsers.add_parser('ManualPrep', help='This command takes user interaction to identify depth crops, RGB crops, and register images')
prepParser.add_argument('-p', '--ProjectIDs', nargs = '+', required = True, type = str, help = 'Manually identify the projects you want to analyze. If All is specified, all non-prepped projects will be analyzed')
prepParser.add_argument('-n', '--Number', type = int, help = 'Use this flag if you only want to analyze a certain number of strains before quitting')

projectParser = subparsers.add_parser('ProjectAnalysis', help='This command performs a single type of analysis of the project. It is meant to be chained together to perform the entire analysis')
projectParser.add_argument('AnalysisType', type = str, choices=['Download','Depth','Cluster','MLClassification', 'MLFishDetection','Backup'], help = 'What type of analysis to perform')
projectParser.add_argument('ProjectID', type = str, help = 'Which projectID you want to identify')
projectParser.add_argument('-w', '--Workers', type = int, help = 'Use if you want to control how many workers this analysis uses', default = 1)
projectParser.add_argument('-g', '--GPUs', type = int, help = 'Use if you want to control how many GPUs this analysis uses', default = 1)
projectParser.add_argument('-d', '--DownloadOnly', action = 'store_true', help = 'Use if you only want to download the data for a specific analysis', default = 1)

totalProjectsParser = subparsers.add_parser('TotalProjectAnalysis', help='This command runs the entire pipeline on list of projectIDs')
totalProjectsParser.add_argument('Computer', type = str, choices=['SRG','PACE'], help = 'What computer are you running this analysis from?')
totalProjectsParser.add_argument('-p', '--ProjectIDs', nargs = '+', required = True, type = str, help = 'Manually identify the projects you want to analyze. If All is specified, all non-prepped projects will be analyzed')

args = parser.parse_args()

if args.command is None:
	parser.print_help()

if args.command == 'UpdateAnalysisSummary':
	
	ap_obj = AP()
	ap_obj.updateAnalysisFile()

if args.command == 'ManualPrep':
	
	projects = parseProjects(args, 'Prep')
	print('Will identify crop and registration for the following projects:' )
	print(projects)

	for projectID in projects:
		pp_obj = PP(args.ProjectID, args.Workers)
		pp_obj.runPrepAnalysis()
		
	updateAnalysisSummary()

if args.command == 'ProjectAnalysis':

	if args.DownloadOnly and args.AnalysisType in ['Download','Backup']:
		print('DownloadOnly flag cannot be used with Download or Backup AnalysisType')
		sys.exit()

	args.ProjectIDs = [args.ProjectID] # format that parseProjects expects
	projects = parseProjects(args, 'Prep')

	pp_obj = PP(args.ProjectID, args.Workers)

	if args.AnalysisType == 'Download' or args.DownloadOnly:
		pp_obj.downloadData(args.AnalysisType)

	elif args.AnalysisType == 'Depth':
		pp_obj.runDepthAnalysis()

	elif args.AnalysisType == 'Cluster':
		pp_obj.runClusterAnalysis()

	elif args.AnalysisType == 'MLClassification':
		pp_obj.runMLCllasification()

	elif args.AnalysisType == 'MLFishDetection':
		pp_obj.runMLFishDetection()

	elif args.AnalysisType == 'Backup':
		pp_obj.backupAnalysis()

if args.command == 'TotalProjectAnalysis':
	projects = parseProjects(args, )



