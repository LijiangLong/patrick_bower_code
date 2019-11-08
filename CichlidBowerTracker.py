import argparse, subprocess, collections, os, pdb, datetime
import pandas as pd
from Modules.MasterAnalysisSummary import MasterAnalysisSummary as MAS
from Modules.DataPreparers.CropPreparer import CropPreparer as CP
from Modules.DataPreparers.DepthPreparer import DepthPreparer as DP
from Modules.DataPreparers.AllVideosPreparer import AllVideosPreparer as AVP

import warnings
warnings.filterwarnings('ignore')


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(help='Available Commands', dest='command')

trackerParser = subparsers.add_parser('CollectData', help='This command runs on Raspberry Pis to collect depth and RGB data')

summarizeParser = subparsers.add_parser('UpdateAnalysisSummary', help='This command identifies any new projects that can be analyzed and merges any updates that are new')

prepParser = subparsers.add_parser('ManualPrep', help='This command takes user interaction to identify depth crops, RGB crops, and register images')
prepParser.add_argument('-p', '--ProjectIDs', nargs = '+', required = True, type = str, help = 'Manually identify the projects you want to analyze. If All is specified, all non-prepped projects will be analyzed')
prepParser.add_argument('-n', '--Number', type = int, help = 'Use this flag if you only want to analyze a certain number of strains before quitting')

depthParser = subparsers.add_parser('DepthPreparer', help='This command takes prepares the depth data for downstream analysis')
depthParser.add_argument('-p', '--ProjectIDs', nargs = '+', required = True, type = str, help = 'Manually identify the projects you want to analyze. If All is specified, all non-prepped projects will be analyzed')
depthParser.add_argument('-n', '--Number', type = int, help = 'Use this flag if you only want to analyze a certain number of strains before quitting')

prepParser = subparsers.add_parser('VideoPreparer', help='This command takes prepares the video data for downstream analysis')
prepParser.add_argument('-p', '--ProjectIDs', nargs = '+', required = True, type = str, help = 'Manually identify the projects you want to analyze. If All is specified, all non-prepped projects will be analyzed')
prepParser.add_argument('-n', '--Number', type = int, help = 'Use this flag if you only want to analyze a certain number of strains before quitting')
prepParser.add_argument('-c', '--noCluster', action = 'store_true', help = 'Use this flag if you do not want to do cluster analysis (assumes it is already done)')
prepParser.add_argument('-m', '--MachineLearning', type = str, help = 'Use this flag if you want to perform machine learning - requres Machine learning model')


args = parser.parse_args()

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

if args.command is None:
	parser.print_help()

if args.command == 'UpdateAnalysisSummary':
	
	updateAnalysisSummary()

if args.command == 'ManualPrep':
	
	projects = parseProjects(args, 'Prep')
	print('Will identify crop and registration for the following projects:' )
	print(projects)

	for projectID in projects:
		cp_obj = CP(projectID)
		cp_obj.prepData()
		
	updateAnalysisSummary()

if args.command == 'DepthPreparer':
	projects = parseProjects(args, 'Depth')
	print('Will build DepthAnalysis files for the following projects:' )
	print(projects)

	for projectID in projects:
		dp_obj = DP(projectID)
		dp_obj.runAnalysis()

	updateAnalysisSummary()

if args.command == 'VideoPreparer':
	projects = parseProjects(args, 'Video')
	print('Will build VideoAnalysis files for the following projects:' )
	print(projects)

	for projectID in projects:
		avp_obj = AVP(projectID)
		if not args.noCluster:
			pass
			avp_obj.prepareAllClusterData()
		if args.MachineLearning is not None:
			avp_obj.prepareAllMLData(args.MachineLearning)
		if not args.noCluster:
			avp_obj.runClusterAnalysis()
		if args.MachineLearning is not None:
			avp_obj.predictClusterLabels(args.MachineLearning)



