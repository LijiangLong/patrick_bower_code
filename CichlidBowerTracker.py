import argparse, os, pdb, sys, subprocess
from Modules.DataPreparers.AnalysisPreparer import AnalysisPreparer as AP
from Modules.DataPreparers.ProjectPreparer import ProjectPreparer as PP


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(help='Available Commands', dest='command')

trackerParser = subparsers.add_parser('CollectData', help='This command runs on Raspberry Pis to collect depth and RGB data')

summarizeParser = subparsers.add_parser('UpdateAnalysisSummary', help='This command identifies any new projects that can be analyzed and merges any updates that are new')

prepParser = subparsers.add_parser('ManualPrep', help='This command takes user interaction to identify depth crops, RGB crops, and register images')
prepParser.add_argument('-p', '--ProjectIDs', nargs = '+', required = True, type = str, help = 'Manually identify the projects you want to analyze. If All is specified, all non-prepped projects will be analyzed')
prepParser.add_argument('-w', '--Workers', type = int, help = 'Use if you want to control how many workers this analysis uses', default = 1)

projectParser = subparsers.add_parser('ProjectAnalysis', help='This command performs a single type of analysis of the project. It is meant to be chained together to perform the entire analysis')
projectParser.add_argument('AnalysisType', type = str, choices=['Download','Depth','Cluster','MLClassification', 'MLFishDetection','Figures','Backup'], help = 'What type of analysis to perform')
projectParser.add_argument('ProjectID', type = str, help = 'Which projectID you want to identify')
projectParser.add_argument('-w', '--Workers', type = int, help = 'Use if you want to control how many workers this analysis uses', default = 1)
projectParser.add_argument('-g', '--GPUs', type = int, help = 'Use if you want to control how many GPUs this analysis uses', default = 1)
projectParser.add_argument('-d', '--DownloadOnly', action = 'store_true', help = 'Use if you only want to download the data for a specific analysis')

totalProjectsParser = subparsers.add_parser('TotalProjectAnalysis', help='This command runs the entire pipeline on list of projectIDs')
totalProjectsParser.add_argument('Computer', type = str, choices=['SRG','PACE'], help = 'What computer are you running this analysis from?')
totalProjectsParser.add_argument('-p', '--ProjectIDs', nargs = '+', required = True, type = str, help = 'Manually identify the projects you want to analyze. If All is specified, all non-prepped projects will be analyzed')
totalProjectsParser.add_argument('-w', '--Workers', type = int, help = 'Use if you want to control how many workers this analysis uses', default = 1)

args = parser.parse_args()

if args.command is None:
	parser.print_help()

if args.command == 'UpdateAnalysisSummary':
	
	ap_obj = AP()
	ap_obj.updateAnalysisFile()

elif args.command == 'ManualPrep':
	
	ap_obj = AP()
	if ap_obj.checkProjects(args.ProjectIDs):
		sys.exit()

	for projectID in args.ProjectIDs:
		pp_obj = PP(projectID, args.Workers)
		pp_obj.runPrepAnalysis()
		
	#pp_obj.backupAnalysis()
	ap_obj.updateAnalysisFile(newProjects = False, projectSummary = False)

elif args.command == 'ProjectAnalysis':

	if args.DownloadOnly and args.AnalysisType in ['Download','Backup']:
		print('DownloadOnly flag cannot be used with Download or Backup AnalysisType')
		sys.exit()

	args.ProjectIDs = args.ProjectID # format that parseProjects expects

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

	elif args.AnalysisType == 'Figures':
		pp_obj.runFigureCreation()

	elif args.AnalysisType == 'Backup':
		pp_obj.backupAnalysis()

if args.command == 'TotalProjectAnalysis':
	ap_obj = AP()
	if ap_obj.checkProjects(args.ProjectIDs):
		sys.exit()

	for projectID in args.ProjectIDs:
		downloadProcess = subprocess.run(['python3', 'CichlidBowerTracker.py', 'ProjectAnalysis', 'Download', projectID])
		depthProcess = subprocess.Popen(['python3', 'CichlidBowerTracker.py', 'ProjectAnalysis', 'Depth', projectID, '-w', '1'])
		clusterProcess = subprocess.Popen(['python3', 'CichlidBowerTracker.py', 'ProjectAnalysis', 'Cluster', projectID, '-w', '23'])
		depthProcess.communicate()
		clusterProcess.communicate()
		mlProcess = subprocess.run(['python3', 'CichlidBowerTracker.py', 'ProjectAnalysis', 'MLClassification', projectID])
		
		#downloadProcess = subprocess.run(['python3', 'CichlidBowerTracker.py', 'ProjectAnalysis', 'Backup', projectID])
	





