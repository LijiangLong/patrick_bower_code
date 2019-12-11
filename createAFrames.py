import subprocess
projects = ['CV_fem_con1','CV_fem_con2','CV_fem_con3','CV_male_con1','CV_male_con2','CV_male_con3','CV_male_con4',
			'CV_social_male_con1','CV_social_male_con1_2','CV_social_male_con2','CV_social_male_con3','CV_social_male_con3_2',
			'MC_fem_con1','MC_fem_con2','MC_fem_con3','MC_male_con1','MC_male_con2','MC_male_con3','MC_male_con4',
			'MC_social_male_con1','MC_social_male_con1_2','MC_social_male_con2','MC_social_male_con3',
			'TI_male_con1','TI_male_con2','TI_social_fem_con1','TI_social_male_con1','TI_social_male_con2']

for projectID in projects:
	print(projectID)
	subprocess.run(['python3', 'CichlidBowerTracker.py', 'ProjectAnalysis', 'Download', projectID])
	subprocess.run(['python3', 'CichlidBowerTracker.py', 'ProjectAnalysis', 'CreateFrames', projectID])
	subprocess.run(['python3', 'CichlidBowerTracker.py', 'ProjectAnalysis', 'Backup', projectID])