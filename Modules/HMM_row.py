import numpy as np

args.Rowfile
args.Window


data = np.load(args.Rowfile)
original_shape = data.shape

data[data == 0] = 1 # 0 used for bad data to save space and use uint8 for storing data (np.nan must be a float)

# Calculate means
lrm = scipy.ndimage.filters.uniform_filter(data, size = (1,args.Window), mode = 'reflect', origin = -1*int(args.Window/2)).astype('uint8')
rrm = np.roll(lrm, int(args.Window), axis = 1).astype('uint8')
rrm[:,0:args.Window] = lrm[:,0:1]

# Identify data that falls outside of mean
data[(((data > lrm + 7.5) & (data > rrm + 7.5)) | ((data < lrm - 7.5) & (data < rrm - 7.5)))] = 0
del lrm, rrm

# Interpolation missing data for HMM
data = data.ravel(order = 'C') #np.interp requires flattend data
nans, x = data==0, lambda z: z.nonzero()[0]
data[nans]= np.interp(x(nans), x(~nans), data[~nans])
del nans, x

# Reshape array to save it
data = np.reshape(data, newshape = original_shape, order = 'C').astype('uint8')
        
zs = np.zeros(shape = data.shape, dtype = 'uint8')
for i, column in enumerate(data):

    means = scipy.ndimage.filters.uniform_filter(column, size = hmm_window, mode = 'reflect').astype('uint8')
    freq, bins = np.histogram(means, bins = range(0,257,2))
    states = bins[0:-1][freq > hmm_window]
    comp = len(states)
    if comp == 0:
        print('For row ' + str(row) + ' and column ' + str(i) + ', states = ' + str(states))
        states = [125]
    model = hmm.GaussianHMM(n_components=comp, covariance_type="spherical")
    model.startprob_ = np.array(comp*[1/comp])
    change = 1/(seconds_to_change)
    trans = np.zeros(shape = (len(states),len(states)))
    for k,state in enumerate(states):
        s_trans = np.zeros(shape = states.shape)
        n_trans_states = np.count_nonzero((states > state + non_transition_bins) | (states < state - non_transition_bins))
        if n_trans_states != 0:
            s_trans[(states > state + non_transition_bins) | (states < state - non_transition_bins)] = change/n_trans_states
            s_trans[states == state] = 1 - change
        else:
            s_trans[states == state] = 1
        trans[k] = s_trans
                   
    model.transmat_ = np.array(trans)
    model.means_ = states.reshape(-1,1)
    model.covars_ = np.array(comp*[std])
            
    z = [model.means_[x][0] for x in model.predict(column.reshape(-1,1))]
    zs[i,:] = np.array(z).astype('uint8')

np.save(self._row_fn(row).replace('.npy', '.hmm.npy'), zs)

for i, column in enumerate(data):
    cpos = 0
    out = []
    split_data = np.split(column, 1 + np.where(np.diff(column) != 0)[0])
    for d in split_data:
        try:
            self.data[self.current_count] = (cpos, cpos + len(d) - 1, d[0])
        except IndexError: # numpy array is too small to hold all the data. Resize it
            self.data = np.resize(self.data, (self.data.shape[0]*5, self.data.shape[1]))
            self.data[self.current_count] = (cpos, cpos + len(d) - 1, d[0])

        cpos = cpos + len(d)
        self.current_count += 1

