import pandas as pd
import numpy as np
from sklearn import cluster
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

'''
This script uses k-means clustering to determine the optimal number of clusters.
We will use this number as the amount of bins we are going to predict
neighborhood demand into. Predicted demand will be split into n different
quantiles.
'''

# Read in the data
data = pd.read_csv('./2014_combined_final.csv')

# Encode the nta column
le = LabelEncoder()
nta_encoded = le.fit_transform(data.nta)
data['nta_encoded'] = nta_encoded

# Drop the columns we won't use for our model
data.drop(['nta','date_hour','nta_dt','nbhd_name','Unnamed: 0'],axis=1,inplace=True)

# Scale our data (not every column needs to be scaled)
to_scale = data[(data.columns-['month','day','hour','nta_encoded'])]
X = StandardScaler().fit_transform(to_scale)
X = pd.DataFrame(X)
for col in ['month','day','hour','nta_encoded']:
    X[col] = data[col]
X = X.as_matrix()

# We want to determine the number of bins we are going to classify into by using
# k-means clustering different values of n clusters. We are going to choose the
# n with the best silhouette score
cluster_scores = []
for n in range(3,6):
    # Initialize and fit a KMeans object
    k_means = cluster.KMeans(n_clusters=n,n_jobs=-1,verbose=1)
    k_means.fit(X)
    # Get the cluster labels for each point
    labels = k_means.labels_
    # Initialize a list to store this n's silhouette scores
    scores = []
    # We need to limit the sample_size when calculating silhouette scores due to
    # computation time
    # We will take 10 different samples of 10,000 points and use the average of
    # those silhouette scores
    for i in range(10):
        score = silhouette_score(X,labels,metric='euclidean',sample_size=10000)
        scores.append(score)
    # Store the average of these silhouette scores
    cluster_scores.append([n,sum(scores)/float(len(scores))])


# Plot the silhouette score as number of clusters increases
plt.plot(cluster_scores[:,0],cluster_scores[:,1])
plt.xlim([3,6])
plt.xlabel('Number of clusters')
plt.ylabel('Silhouette score')
# We see that n=3 gives us the best silhouette score
