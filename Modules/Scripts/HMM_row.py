import argparse, pdb, os, subprocess
os.environ["OMP_NUM_THREADS"] = "1" # export OMP_NUM_THREADS=4
os.environ["OPENBLAS_NUM_THREADS"] = "1" # export OPENBLAS_NUM_THREADS=4 
os.environ["MKL_NUM_THREADS"] = "1" # export MKL_NUM_THREADS=6
os.environ["VECLIB_MAXIMUM_THREADS"] = "1" # export VECLIB_MAXIMUM_THREADS=4
os.environ["NUMEXPR_NUM_THREADS"] = "1" # export NUMEXPR_NUM_THREADS=6
import numpy as np
import scipy.ndimage.filters
from hmmlearn import hmm
import warnings
warnings.filterwarnings('ignore')


parser = argparse.ArgumentParser(description='This command runs HMM analysis on a single row of data.')
parser.add_argument('Rowfile', type = str, help = 'The name of the numpy file that will be analyzed')
args = parser.parse_args()

# Define parameters
mean_window = 120 # How many seconds to calculate means for filtering out noisy data
mean_cushion = 7.5
hmm_window = 60 # Used for reducing the number of states for HMM calculation
seconds_to_change = 60*30 # Used to determine expectation of transition from one state to another (i.e. how many manipulations occur)
non_transition_bins = 2 # Parameter to prevent small changes in state
std = 100 # Standard deviation of data
row = int(args.Rowfile.split('/')[-1].split('.')[0])

data = np.load(args.Rowfile)
original_shape = data.shape

data[data == 0] = 1 # 0 used to indicate data outside of mean value that needs to be interpolated; using uint8 to save space

# Calculate means over mean_window parameter
lrm = scipy.ndimage.filters.uniform_filter(data, size = (1,mean_window), mode = 'reflect', origin = -1*int(mean_window/2)).astype('uint8') # Mean from before 
rrm = np.roll(lrm, int(mean_window), axis = 1).astype('uint8') # Mean from after
rrm[:,0:mean_window] = lrm[:,0:1] # Deal with boundaries

# Identify data that falls outside of mean using 7.5 cushion
data[(((data > lrm + mean_cushion) & (data > rrm + mean_cushion)) | ((data < lrm - mean_cushion) & (data < rrm - mean_cushion)))] = 0 # Set noisy data to zero
del lrm, rrm #We can delete these arrays now that we are done with them

# Interpolation noisy data for HMM
data = data.ravel(order = 'C') #np.interp requires flattend data
nans, x = data==0, lambda z: z.nonzero()[0]
data[nans]= np.interp(x(nans), x(~nans), data[~nans]) # position of missing data, position of non-missing data, value of non-missing data
data = np.reshape(data, newshape = original_shape, order = 'C').astype('uint8') # Reshape data back to original shape
del nans, x # Can delete these now that we are done with interpolation
		
# Calculate HMM for each column in the row
#zs = np.zeros(shape = data.shape, dtype = 'uint8') # 
for i, column in enumerate(data): # Iterate through each column

	# In order to save time for the HMM calculation, we only use states that are commonly found
	means = scipy.ndimage.filters.uniform_filter(column, size = hmm_window, mode = 'reflect').astype('uint8')
	freq, bins = np.histogram(means, bins = range(0,257,2))
	states = bins[0:-1][freq > hmm_window]
	n_states = len(states)

	# Calculate HMM
	model = hmm.GaussianHMM(n_components=n_states, covariance_type="spherical")
	model.startprob_ = np.array(n_states*[1/n_states])
	change = 1/(seconds_to_change) # probability of transitioning states

	# Create transition matrix
	trans = np.zeros(shape = (n_states, n_states))
	for k,state in enumerate(states):
		s_trans = np.zeros(shape = states.shape) # Create row
		n_trans_states = np.count_nonzero((states > state + non_transition_bins) | (states < state - non_transition_bins))
		if n_trans_states != 0:
			s_trans[(states > state + non_transition_bins) | (states < state - non_transition_bins)] = change/n_trans_states
			s_trans[states == state] = 1 - change
		else:
			s_trans[states == state] = 1
		trans[k] = s_trans
				 
	# Set various values of HMM model  
	model.transmat_ = np.array(trans)
	model.means_ = states.reshape(-1,1)
	model.covars_ = np.array(n_states*[std])
			
	# Calculate HMM
	z = [model.means_[x][0] for x in model.predict(column.reshape(-1,1))]
	
	# Overwrite data with new HMM data
	data[i,:] = np.array(z).astype('uint8')
np.save(args.Rowfile.replace('.npy', '.hmm.bu.npy'), data)

# Create array to save data
# In order to save space, we only store when data is the same (first_t, last_t, hmm_state)

out_data = np.zeros(shape = (3000,6), dtype = 'uint16') # Initially create an array for 3000 transitions
transition = 0
for i, column in enumerate(data):
	cpos = 0
	split_data = np.split(column, 1 + np.where(np.diff(column) != 0)[0])
	for j,d in enumerate(split_data):
		if j==0:
			change = 0
		else:
			change = abs(prev_mag - d[0])
		try:
			out_data[transition] = (cpos, cpos + len(d) - 1, d[0], row, i, change)
		except IndexError: # numpy array is too small to hold all the data. Resize it
			out_data = np.resize(out_data, (out_data.shape[0]*5, out_data.shape[1]))
			out_data[transition] = (cpos, cpos + len(d) - 1, d[0], row, i, change)
		prev_mag = d[0]
		cpos = cpos + len(d)
		transition += 1
out_data = np.delete(out_data, range(transition, out_data.shape[0]), axis = 0)
np.save(args.Rowfile.replace('.npy', '.hmm.npy'), out_data)
#subprocess.run(['rm', '-f', args.Rowfile])
