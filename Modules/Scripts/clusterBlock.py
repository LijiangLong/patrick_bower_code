import argparse

parser = argparse.ArgumentParser(description='This command runs HMM analysis on a single row of data.')
parser.add_argument('npyFile', type = str, help = 'The name of the numpy file that will be analyzed')
parser.add_argument('treeR', type = str, help = 'The name of the numpy file that will be analyzed')
parser.add_argument('leafNum', type = str, help = 'The name of the numpy file that will be analyzed')
parser.add_argument('minPts', type = str, help = 'The name of the numpy file that will be analyzed')

args = parser.parse_args()


X = NearestNeighbors(radius=self.projFileManager.treeR, metric='minkowski', p=2, algorithm='kd_tree',leaf_size=self.projFileManager.leafNum,n_jobs=24).fit(sortData[min_index:max_index]
dist = X.radius_neighbors_graph(sortData[min_index:max_index], self.projFileManager.neighborR, 'distance')
sub_label = DBSCAN(eps=self.projFileManager.eps, min_samples=self.projFileManager.minPts, metric='precomputed', n_jobs=self.workers).fit_predict(dist)
new_labels = int(sub_label.max()) + 1
sub_label[sub_label != -1] += curr_label
labels[min_index:max_index,0] = sub_label
curr_label += new_labels
