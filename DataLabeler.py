import argparse, os, pdb, sys
from Modules.DataPreparers.AnalysisPreparer import AnalysisPreparer as AP
from Modules.DataPreparers.LabelPreparer import LabelPreparer as LP


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(help='Available Commands', dest='command')

clipParser = subparsers.add_parser('LabelClips', help='This command is used to label video clips for a project')
clipParser.add_argument('ProjectID', type = str, help = 'Which project to label data from')
clipParser.add_argument('Number', type = int, help = 'Number of clips you would like to label')
clipParser.add_argument('-b', '--Backup', action = 'store_true', help = 'Use if something went wrong during labeling and you need to backup all the labels you created', default = 1)
clipParser.add_argument('-i', '--Initials', type = str, help = 'Use if you want to make independent labels', default = 1)

detectParser = subparsers.add_parser('DetectFish', help='This command is used to draw boxes around fish for a project')
detectParser.add_argument('ProjectID', type = str, help = 'Which project to label data from')
detectParser.add_argument('Number', type = int, help = 'Number of clips you would like to label')
detectParser.add_argument('-b', '--Backup', action = 'store_true', help = 'Use if something went wrong during labeling and you need to backup all the labels you created', default = 1)
detectParser.add_argument('-i', '--Initials', type = str, help = 'Use if you want to make independent labels', default = 1)

args = parser.parse_args()

if args.command is None:
	parser.print_help()

elif args.command == 'DetectFish':
	args.ProjectIDs = args.ProjectID

	ap_obj = AP()
	if ap_obj.checkProjects(args.ProjectIDs, 'Cluster'):
		sys.exit()

	pl_obj = LP(projectID, args.Workers)
	pl_obj.labelClips()
