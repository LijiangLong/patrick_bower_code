from Modules.LogParser import LogParser as LP
from Modules.DepthAnalyzer import DepthAnalyzer as DA
import matplotlib.pyplot as plt
import pandas as pd
import datetime

class FigureMaker:
	# This class takes in directory information and a logfile containing depth information and performs the following:
	# 1. Identifies tray using manual input
	# 2. Interpolates and smooths depth data
	# 3. Automatically identifies bower location
	# 4. Analyze building, shape, and other pertinent info of the bower

	def __init__(self, fileManager):
		self.fileManager = fileManager
		self.lp = LP(self.fileManager.localLogfile)
		self.da_obj = DA(self.fileManager)
			
	def createDepthFigures(self, hourlyDelta = 2):

		# Create summary figure of daily values
		figDaily = plt.figure(figsize = (11,8.5)) 
		figDaily.suptitle(self.lp.projectID + ' DailySummary')
		gridDaily = plt.GridSpec(10, self.lp.numDays*4, wspace=0.02, hspace=0.02)

		# Create summary figure of hourly values
		figHourly = plt.figure(figsize = (11,8.5)) 
		figHourly.suptitle(self.lp.projectID + ' HourlySummary')
		gridHourly = plt.GridSpec(self.lp.numDays, int(24/hourlyDelta) + 2, wspace=0.02, hspace=0.02)

		start_day = self.lp.frames[0].time.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
		totalChangeData = self.da_obj.returnVolumeSummary(self.lp.frames[0].time, self.lp.frames[-1].time)

		# Show picture of final depth
		topAx1 = figDaily.add_subplot(gridDaily[0:2, 0:self.lp.numDays*1-1])
		topAx1_ax = topAx1.imshow(self.da_obj.returnHeight(self.lp.frames[-1].time, cropped = True), vmin = 50, vmax = 70)
		topAx1.set_title('Final depth (cm)')
		topAx1.set_xticklabels([])
		topAx1.set_yticklabels([])
		plt.colorbar(topAx1_ax, ax = topAx1)

		# Show picture of total depth change
		topAx2 = figDaily.add_subplot(gridDaily[0:2, self.lp.numDays*1:self.lp.numDays*2-1])
		topAx2_ax = topAx2.imshow(self.da_obj.returnHeightChange(self.lp.frames[0].time, self.lp.frames[-1].time, cropped = True), vmin = -5, vmax = 5)
		topAx2.set_title('Total depth change (cm)')
		topAx2.set_xticklabels([])
		topAx2.set_yticklabels([])
		plt.colorbar(topAx2_ax, ax = topAx2)

		# Show picture of pit and castle mask
		topAx3 = figDaily.add_subplot(gridDaily[0:2, self.lp.numDays*2:self.lp.numDays*3-1])
		topAx3_ax = topAx3.imshow(self.da_obj.returnHeightChange(self.lp.frames[0].time, self.lp.frames[-1].time, cropped = True, masked = True), vmin = -5, vmax = 5)
		topAx3.set_title('Mask')
		topAx3.set_xticklabels([])
		topAx3.set_yticklabels([])
		#plt.colorbar(topAx3_ax, ax = topAx3)

		# Bower index based upon higher thresholds
		"""topAx4 = figDaily.add_subplot(gridDaily[0:2, self.lp.numDays*3:self.lp.numDays*4])
		x_values = [1.0, 3.0, 5.0]
		y_values = []
		for thresh in x_values:
			tdata = self._summarizeBuilding(self.lp.frames[0].time, self.lp.frames[-1].time, totalThreshold = thresh)
			y_values.append(tdata['bowerIndex'])
			totalChangeData['bowerIndex_' + str(thresh)] = tdata['bowerIndex']
		topAx4.plot(x_values, y_values)
		topAx4.set_title('BowerIndex vs. Threshold (cm)')
		figDaily.tight_layout()    """

		# Create figures and get data for daily Changes
		dailyChangeData = []
		for i in range(self.lp.numDays):
			if i == 0:
				current_ax = [figDaily.add_subplot(gridDaily[3, i*4:i*4+3])]
				current_ax2 = [figDaily.add_subplot(gridDaily[4, i*4:i*4+3], sharex = current_ax[i])]
				current_ax3 = [figDaily.add_subplot(gridDaily[5, i*4:i*4+3], sharex = current_ax[i])]
				
			else:
				current_ax.append(figDaily.add_subplot(gridDaily[3, i*4:i*4+3], sharey = current_ax[0]))
				current_ax2.append(figDaily.add_subplot(gridDaily[4, i*4:i*4+3], sharex = current_ax[i], sharey = current_ax2[0]))
				current_ax3.append(figDaily.add_subplot(gridDaily[5, i*4:i*4+3], sharex = current_ax[i], sharey = current_ax3[0]))
				
			start = start_day + datetime.timedelta(hours = 24*i)
			stop = start_day + datetime.timedelta(hours = 24*(i+1))
			
			dailyChangeData.append(vars(self.da_obj.returnVolumeSummary(start,stop)))
			dailyChangeData[i]['Day'] = i+1
			dailyChangeData[i]['Midpoint'] = i+1 + .5
			dailyChangeData[i]['StartTime'] = str(start)

			current_ax[i].set_title('Day ' + str(i+1))

			current_ax[i].imshow(self.da_obj.returnHeightChange(start_day, stop, cropped = True), vmin = -2, vmax = 2)
			current_ax2[i].imshow(self.da_obj.returnHeightChange(start, stop, cropped = True), vmin = -2, vmax = 2)
			current_ax3[i].imshow(self.da_obj.returnHeightChange(start, stop, masked = True, cropped = True), vmin = -2, vmax = 2)
		   
			current_ax[i].set_xticklabels([])
			current_ax2[i].set_xticklabels([])
			current_ax3[i].set_xticklabels([])

			current_ax[i].set_yticklabels([])
			current_ax2[i].set_yticklabels([])
			current_ax3[i].set_yticklabels([])

			current_ax[i].set_adjustable('box')
			current_ax2[i].set_adjustable('box')
			current_ax3[i].set_adjustable('box')

		figDaily.tight_layout()
		hourlyChangeData = []

		for i in range(0, self.lp.numDays):
			for j in range(int(24/hourlyDelta)):
				start = start_day + datetime.timedelta(hours = 24*i + j*hourlyDelta)
				stop = start_day + datetime.timedelta(hours = 24*i + (j+1)*hourlyDelta)

				hourlyChangeData.append(vars(self.da_obj.returnVolumeSummary(start,stop)))
				hourlyChangeData[-1]['Day'] = i+1
				hourlyChangeData[-1]['Midpoint'] = i+1 + ((j + 0.5) * hourlyDelta)/24
				hourlyChangeData[-1]['StartTime'] = str(start)

				current_ax = figHourly.add_subplot(gridHourly[i, j])

				current_ax.imshow(self.da_obj.returnHeightChange(start, stop, cropped = True), vmin = -1, vmax = 1)
				current_ax.set_adjustable('box')
				current_ax.set_xticklabels([])
				current_ax.set_yticklabels([])
				if i == 0:
					current_ax.set_title(str(j*hourlyDelta) + '-' + str((j+1)*hourlyDelta))

			current_ax = figHourly.add_subplot(gridHourly[i, int(24/hourlyDelta)])
			current_ax.imshow(self.da_obj.returnBowerLocations(stop - datetime.timedelta(hours = 24), stop, cropped = True), vmin = -1, vmax = 1)
			current_ax.set_adjustable('box')
			current_ax.set_xticklabels([])
			current_ax.set_yticklabels([])
			if i==0:
				current_ax.set_title('DMask')


			current_ax = figHourly.add_subplot(gridHourly[i, int(24/hourlyDelta)+1])
			current_ax.imshow(self.da_obj.returnHeightChange(stop - datetime.timedelta(hours = 24), stop, cropped = True), vmin = -1, vmax = 1)
			current_ax.set_adjustable('box')
			current_ax.set_xticklabels([])
			current_ax.set_yticklabels([])
			if i==0:
				current_ax.set_title('DChange')

		totalDT = pd.DataFrame([totalChangeData])
		dailyDT = pd.DataFrame(dailyChangeData)
		hourlyDT = pd.DataFrame(hourlyChangeData)

		writer = pd.ExcelWriter(self.fileManager.localFigureDir + 'DataSummary.xlsx')
		totalDT.to_excel(writer,'Total')
		dailyDT.to_excel(writer,'Daily')
		hourlyDT.to_excel(writer,'Hourly')
		writer.save()

		volAx = figDaily.add_subplot(gridDaily[6:8, 0:self.lp.numDays*4])
		volAx.plot(dailyDT['Midpoint'], dailyDT['bowerVolume'])
		volAx.plot(hourlyDT['Midpoint'], hourlyDT['bowerVolume'])
		volAx.set_ylabel('Volume Change')

		bIAx = figDaily.add_subplot(gridDaily[8:10, 0:self.lp.numDays*4], sharex = volAx)
		bIAx.scatter(dailyDT['Midpoint'], dailyDT['bowerIndex'])
		bIAx.scatter(hourlyDT['Midpoint'], hourlyDT['bowerIndex'])
		bIAx.set_xlabel('Day')
		bIAx.set_ylabel('Bower Index')



		figDaily.savefig(self.fileManager.localFigureDir + 'DailyDepthSummary.pdf')  
		figHourly.savefig(self.fileManager.localFigureDir + 'HourlyDepthSummary.pdf')  

		plt.clf()

	