import matplotlib.pyplot as plt
# These disable some of the default key strokes that we will use
plt.rcParams['keymap.all_axes'] = '' #a
plt.rcParams['keymap.back'] = ['left', 'backspace', 'MouseButton.BACK'] #c
plt.rcParams['keymap.fullscreen'] = '' #f
plt.rcParams['keymap.pan'] = '' #p
plt.rcParams['keymap.save'] = '' #s
plt.rcParams['keymap.zoom'] = '' #o
plt.rcParams['keymap.xscale'] = ['L'] #k

# Import buttons that we will use to make this interactive
from matplotlib.widgets import Button
from matplotlib.widgets import RadioButtons
from matplotlib.widgets import RectangleSelector
from matplotlib.widgets import PolygonSelector

# Import some patches that we will use to display the annotations
from matplotlib.patches import Rectangle
from matplotlib.patches import Circle

import pdb, datetime, os
import pandas as pd

class Annotation():
	def __init__(self, other):
		self.other = other
		self.sex = ''
		self.coords = ()
		self.poses = ()
		self.rectangle = None
		self.circles = []

	def addRectangle(self):
		if self.rectangle is None:
			self.rectangle = Rectangle((self.coords[0], self.coords[1]), self.coords[2], self.coords[3],
										fill = False, edgecolor = 'green', linewidth = 1.4, figure = self.other.fig)
			self.other.ax_image.add_patch(self.rectangle)
			self.other.cur_text.set_text('BB: ' + str(self.coords))
		else:
			self.other.error_text.set_text('Error: Rectangle already exists')

	def addCircles(self):
		if self.circles ==[]:
			for pose in self.poses:
				self.circles.append(Circle((pose[0],pose[1]), radius = 10, figure = self.other.fig))
				self.other.ax_image.add_patch(self.circles[-1])

			out_text = 'BB: ' + str(self.coords) + '\n'
			out_text += 'Nose: ' + str(self.poses[0]) + '\n'
			out_text += 'Left eye: ' + str(self.poses[1]) + '\n'
			out_text += 'Tail: ' + str(self.poses[2]) + '\n'
			out_text += 'Right eye: ' + str(self.poses[3])
			self.other.cur_text.set_text(out_text)
		else:
			self.other.error_text.set_text('Error: Poses already exist')

	def removePatches(self):
		try:
			self.other.ax_image.patches.remove(self.rectangle)
		except ValueError:
			pass
		for circle in self.circles:
			try:
				self.other.ax_image.patches.remove(circle)
			except ValueError:
				pass

	def retRow(self):
		if self.coords == ():
			return 'Must create bounding box before saving an annotation'
		elif self.poses == () and self.sex != 'o':
			return 'Must identify body parts on non-occluded animals'
		elif self.sex == 'o':
			return [self.other.frames[self.other.frame_index], self.sex, self.coords, '','','','', self.other.user, self.other.now]
		else:
			return [self.other.frames[self.other.frame_index], self.sex, self.coords, self.poses[0], self.poses[1], self.poses[3], self.poses[2], self.other.user, self.other.now]

	def reset(self):
		self.sex = ''
		self.coords = ()
		self.poses = ()
		self.rectangle = None
		self.circles = []

class ObjectLabeler():
	def __init__(self, frameDirectory, annotationFile):

		self.frameDirectory = frameDirectory
		self.annotationFile = annotationFile
		self.frames = [x for x in os.listdir(self.frameDirectory) if '.jpg' in x]
		assert len(self.frames) > 0

		# Initialize flag to keep track of whether the user is drawing and object box
		self.drawing = False

		# Keep track of the frame we are on
		self.frame_index = 0

		# Intialize lists to hold annotated objects
		self.coords = ()
		self.poses = () 

		# Create dataframe to hold annotations
		if os.path.exists(self.annotationFile):
			self.dt = pd.read_csv(self.annotationFile)
		else:
			self.dt = pd.DataFrame(columns=['Framefile', 'Nfish', 'Sex', 'Box', 'Nose', 'LEye', 'REye', 'Tail', 'User', 'DateTime'])
		self.f_dt = pd.DataFrame(columns=['Framefile','Sex', 'Box', 'Nose', 'LEye', 'REye', 'Tail', 'User', 'DateTime'])

		# Get user and current time
		self.user = os.getenv('USER')
		self.now = datetime.datetime.now()

		# Create Annotation object
		self.annotation = Annotation(self)

		# Start figure
		self._createFigure()

	def _createFigure(self):
		# Create figure
		self.fig = fig = plt.figure(1, figsize=(10,7))

		# Create image subplot
		self.ax_image = fig.add_axes([0.05,0.2,.8,0.75])
		while len(self.dt[(self.dt.Framefile == self.frames[self.frame_index]) & (self.dt.User == self.user)]) != 0:
			self.frame_index += 1
		img = plt.imread(self.frameDirectory + self.frames[self.frame_index])
		self.image_obj = self.ax_image.imshow(img)
		self.ax_image.set_title(self.frames[0])

		# Create selectors for identifying bounding bos and body parts (nose, left eye, right eye, tail)
		self.PS = PolygonSelector(self.ax_image, self._grabPoses,
									   useblit=True )
		self.PS.set_active(False)

		self.RS = RectangleSelector(self.ax_image, self._grabBoundingBox,
									   drawtype='box', useblit=True,
									   button=[1, 3],  # don't use middle button
									   minspanx=5, minspany=5,
									   spancoords='pixels',
									   interactive=True)
		self.RS.set_active(True)

		# Create radio buttons
		self.ax_radio = fig.add_axes([0.85,0.85,0.125,0.1])
		self.radio_names = [r"$\bf{M}$" + 'ale',r"$\bf{F}$" + 'emale',r"$\bf{O}$" +'ccluded',r"$\bf{U}$" +'nknown']
		self.bt_radio =  RadioButtons(self.ax_radio, self.radio_names, active=0, activecolor='blue' )

		# Create click buttons for adding annotations
		self.ax_box = fig.add_axes([0.85,0.775,0.125,0.04])
		self.ax_pose = fig.add_axes([0.85,0.725,0.125,0.04])
		self.bt_box = Button(self.ax_box, 'Add ' + r"$\bf{B}$" + 'ox')
		self.bt_poses = Button(self.ax_pose, 'Add ' + r"$\bf{P}$" + 'ose')
		
		# Create click buttons for keeping or clearing annotations
		self.ax_anAdd = fig.add_axes([0.85,0.525,0.125,0.04])
		self.ax_anClear = fig.add_axes([0.85,0.475,0.125,0.04])
		self.bt_anAdd = Button(self.ax_anAdd, r"$\bf{K}$" + 'eep Ann')
		self.bt_anClear = Button(self.ax_anClear, r"$\bf{C}$" + 'lear Ann')

		# Create click buttons for saving frame annotations or starting over
		self.ax_frameAdd = fig.add_axes([0.85,0.225,0.125,0.04])
		self.ax_frameClear = fig.add_axes([0.85,0.175,0.125,0.04])
		self.bt_frameAdd = Button(self.ax_frameAdd, r"$\bf{N}$" + 'ext Frame')
		self.bt_frameClear = Button(self.ax_frameClear, r"$\bf{R}$" + 'estart')

		# Add text boxes to display info on annotations
		self.ax_cur_text = fig.add_axes([0.85,0.575,0.125,0.14])
		self.ax_cur_text.set_axis_off()
		self.cur_text =self.ax_cur_text.text(0, 1, '', fontsize=9, verticalalignment='top')

		self.ax_all_text = fig.add_axes([0.85,0.275,0.125,0.19])
		self.ax_all_text.set_axis_off()
		self.all_text =self.ax_all_text.text(0, 1, '', fontsize=9, verticalalignment='top')

		self.ax_error_text = fig.add_axes([0.1,0.05,.7,0.1])
		self.ax_error_text.set_axis_off()
		self.error_text =self.ax_error_text.text(0, 1, 'TEST', fontsize=14, color = 'red', verticalalignment='top')


		# Set buttons in active that shouldn't be pressed
		#self.bt_poses.set_active(False)
		
		# Turn on keypress events to speed things up
		self.fig.canvas.mpl_connect('key_press_event', self._keypress)

		# Turn off hover event for buttons (no idea why but this interferes with the image rectange remaining displayed)
		self.fig.canvas.mpl_disconnect(self.bt_box.cids[2])
		self.fig.canvas.mpl_disconnect(self.bt_poses.cids[2])
		self.fig.canvas.mpl_disconnect(self.bt_anAdd.cids[2])
		self.fig.canvas.mpl_disconnect(self.bt_anClear.cids[2])
		self.fig.canvas.mpl_disconnect(self.bt_frameAdd.cids[2])
		self.fig.canvas.mpl_disconnect(self.bt_frameClear.cids[2])

		# Connect buttons to specific functions		
		self.bt_box.on_clicked(self._addBoundingBox)
		self.bt_poses.on_clicked(self._addPose)
		self.bt_anAdd.on_clicked(self._saveAnnotation)
		self.bt_anClear.on_clicked(self._clearAnnotation)
		self.bt_frameAdd.on_clicked(self._nextFrame)
		self.bt_frameClear.on_clicked(self._clearFrame)

		# Show figure
		plt.show()

	def _grabBoundingBox(self, eclick, erelease):
		self.error_text.set_text('')

		# Transform and store image coords
		image_coords = list(self.ax_image.transData.inverted().transform((eclick.x, eclick.y))) + list(self.ax_image.transData.inverted().transform((erelease.x, erelease.y)))
		
		# Convert to integers:
		image_coords = tuple([int(x) for x in image_coords])

		xy = (min(image_coords[0], image_coords[2]), min(image_coords[1], image_coords[3]))
		width = abs(image_coords[0] - image_coords[2])
		height = abs(image_coords[1] - image_coords[3])
		self.annotation.coords = xy + (width, height)

	def _grabPoses(self, event):
		self.error_text.set_text('')

		if len(event) != 4:
			self.error_text.set_text('Error: must have exactly four points selected. Try again')

			self.PS._xs, self.PS._ys = [0], [0]
			self.PS._polygon_completed = False
		else:
			self.annotation.poses = tuple([(int(x[0]),int(x[1])) for x in event])

	def _keypress(self, event):
		if event.key in ['m', 'f', 'o', 'u']:
			self.bt_radio.set_active(['m', 'f', 'o', 'u'].index(event.key))
			#self.fig.canvas.draw()
		elif event.key == 'b':
			self._addBoundingBox(event)
		elif event.key == 'p':
			self._addPose(event)	
		elif event.key == 'k':
			self._saveAnnotation(event)
		elif event.key == 'c':
			self._clearAnnotation(event)
		elif event.key == 'n':
			self._nextFrame(event)
		elif event.key == 'r':
			self._clearFrame(event)
		else:
			pass

	def _addBoundingBox(self, event):
		if self.annotation.coords == ():
			self.error_text.set_text('Error: Bounding box not set')
			self.fig.canvas.draw()

			self.RS.set_active(True)
			self.PS.set_active(False)
			return

		# Add new patch rectangle
		#colormap = {self.radio_names[0]:'blue', self.radio_names[1]:'pink', self.radio_names[2]: 'red', self.radio_names[3]: 'black'}
		#color = colormap[self.bt_radio.value_selected]
		self.annotation.addRectangle()
		self.fig.canvas.draw()

		# Change to pose selection
		self.RS.set_active(False)
		self.PS.set_active(True)
		#self.bt_poses.set_active(True) # Need to save bounding box before you can select poses
		#self.bt_box.set_active(False) # Need to save bounding box before you can select poses

	def _addPose(self, event):
		if self.annotation.poses == ():
			self.error_text.set_text('Error: Poses not set')
			self.fig.canvas.draw()

			self.RS.set_active(False)
			self.PS.set_active(True)
			return

		#print(self.poses)
		#self.img_annotations.add(self.xy + (self.width, self.height))
		self.annotation.addCircles()
		self.fig.canvas.draw()

		self.PS._xs, self.PS._ys = [0], [0]
		self.PS._polygon_completed = False

		# Change to box selection
		self.RS.set_active(False)
		self.PS.set_active(False)

	def _saveAnnotation(self, event):

		displayed_names = [r"$\bf{M}$" + 'ale',r"$\bf{F}$" + 'emale',r"$\bf{O}$" +'ccluded',r"$\bf{U}$" +'nknown']
		stored_names = ['m','f','o','u']
		
		self.annotation.sex = stored_names[displayed_names.index(self.bt_radio.value_selected)]

		outrow = self.annotation.retRow()

		if type(outrow) == str:
			self.error_text.set_text(outrow)
			self.fig.canvas.draw()
			self.RS.set_active(False)
			self.PS.set_active(True)
			return
		else:
			self.f_dt.loc[len(self.f_dt)] = outrow

		# Add annotation to the temporary data frame
		self.cur_text.set_text('')
		self.all_text.set_text('# Ann = ' + str(len(self.f_dt)))

		self.annotation.reset()

		self.fig.canvas.draw()

		self.RS.set_active(True)
		self.PS.set_active(False)


	def _clearAnnotation(self, event):

		print(self.ax_image.patches)
		self.annotation.removePatches()
		
		print(self.ax_image.patches)

		self.annotation.reset()

		self.cur_text.set_text('')
		
		self.fig.canvas.draw()

		self.RS.set_active(True)
		self.PS.set_active(False)

	def _nextFrame(self, event):

		if len(self.f_dt) == 0:
			self.f_dt.loc[0] = [self.frames[self.frame_index],'','','','','','',self.user, self.now]
			self.f_dt['Nfish'] = 0
		else:
			self.f_dt['Nfish'] = len(self.f_dt)
		self.dt = self.dt.append(self.f_dt, sort=True)
		# Save dataframe (in case user quits)
		self.dt.to_csv(self.annotationFile, sep = ',')
		self.f_dt = pd.DataFrame(columns=['Framefile','Sex', 'Box', 'Nose', 'LEye', 'REye', 'Tail', 'User', 'DateTime'])


		# Remove old patches
		self.ax_image.patches = []

		# Reset annotations
		self.annotation.reset()

		# Update frame index and determine if all images are annotated
		self.frame_index += 1
		while len(self.dt[(self.dt.Framefile == self.frames[self.frame_index]) & (self.dt.User == self.user)]) != 0:
			self.frame_index += 1

		if self.frame_index == len(self.frames):

			# Disconnect connections and close figure
			plt.close(self.fig)

		self.cur_text.set_text('')
		self.all_text.set_text('')

		# Load new image and save it as the background
		img = plt.imread(self.frameDirectory + self.frames[self.frame_index])
		self.image_obj.set_array(img)
		self.ax_image.set_title(self.frames[self.frame_index])
		self.fig.canvas.draw()
		#self.background = self.fig.canvas.copy_from_bbox(self.fig.bbox)
		self.RS.set_active(True)
		self.PS.set_active(False)


	def _clearFrame(self, event):
		self.f_dt = pd.DataFrame(columns=['Framefile','Sex', 'Box', 'Nose', 'LEye', 'REye', 'Tail', 'User', 'DateTime'])
		# Remove old patches
		self.ax_image.patches = []

		self.fig.canvas.draw()

		# Reset annotations
		self.annotation.reset()
		self.RS.set_active(True)
		self.PS.set_active(False)



obj = ObjectLabeler('MLFrames/', 'AnnotatationFile.csv')
