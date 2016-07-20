import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.base import TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.cross_validation import train_test_split
from sklearn.grid_search import GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.metrics import accuracy_score

# Read in our data
data = pd.read_csv('/Users/Brian/Uber (not on github)/2014_manhattan_classified.csv')
# Drop the columns we won't use in our model
data.drop(['date_hour','nta_dt','month','day','Unnamed: 0','nbhd_name','rides_pct'],axis=1,inplace=True)

# Select the features
X = data[data.columns - ['classification']]
# Select the target
y = data['classification']

# Re-order the columns so the ones that aren't going to be scaled are at the end
nonscale_cols = ['nta','hour','week_day']
cols = [col for col in X if col not in nonscale_cols] + nonscale_cols
X = X[cols]
# Create dummy columns for the nta
X = pd.get_dummies(X,columns=['nta'],drop_first=True)
X = X.as_matrix()

# Create a Class that we will use to scale our columns in a pipeline.
# It will only scale columns that aren't 'hour', 'week_day', or the nta dummy
# columns
class CustomScaler(TransformerMixin):
    def __init__(self):
        self.scaler = StandardScaler()

    def fit(self,X,y):
        self.scaler.fit(X[:,-29:],y)
        return self

    def transform(self,X):
        X_scaled = self.scaler.transform(X[:,-29:])
        # return np.concatenate((X_scaled, X[:,:3]),axis=1)
        X = np.concatenate((X_scaled, X[:,-29:]),axis=1)
        return X

    def get_params(self,deep=True):
        return {}

# Split our data into training and testing sets
X_train,X_test,y_train,y_test = train_test_split(X,y,test_size=.3,random_state=87)

# This function will scale our training and testing sets that we will use to fit
# our models and predict (after finding the optimal parameters w/ GridSearchCV)
def scale_train_test(X_train,y_train,X_test):
    customscaler = CustomScaler()
    customscaler.fit(X_train,y_train)
    X_train_scaled = customscaler.transform(X_train)
    X_test_scaled = customscaler.transform(X_test)
    return X_train_scaled, X_test_scaled

# This function will evaluate a model by fitting on the entire training set and
# then predicting the testing set
def evaluate_model(model, model_type):
    X_train_scaled, X_test_scaled = scale_train_test(X_train,y_train,X_test)
    model.fit(X_train_scaled,y_train)
    predictions = model.predict(X_test_scaled)
    acc = accuracy_score(y_test,predictions)
    print 'Accuracy for %s: %.4f' % (model_type,acc)


# Logistic Regression
params = {'model__penalty':['l1','l2'],'model__C':[.1,1,10]}
pipe = Pipeline([('scale',CustomScaler()),('model',LogisticRegression())])
grid = GridSearchCV(pipe,param_grid=params,cv=3,n_jobs=-1,verbose=1)
grid.fit(X_train,y_train)
print 'Best params for LogReg: %s' % str(grid.best_params_)
# Intialize a new LogisticRegression with the optimal parameters
log = LogisticRegression(C=.1,penalty='l1')
evaluate_model(log,'Logistic Regression')
# Accuracy for Logistic Regression: 0.7893

# K-Nearest Neighbors
params = {'model__n_neighbors':range(2,11),'model__p':[1,2],
          'model__weights':['uniform','distance']}
pipe = Pipeline([('scale',CustomScaler()),('model',KNeighborsClassifier())])
grid = GridSearchCV(pipe,param_grid=params,cv=3,n_jobs=-1,verbose=1)
grid.fit(X_train,y_train)
print 'Best params for kNN: %s' % str(grid.best_params_)
# Intialize a new KNeighborsClassifier with the optimal parameters
knn = KNeighborsClassifier(n_neighbors=10,p=1,weights='uniform')
evaluate_model(knn,'k-Nearest Neighbors')
# Accuracy for k-Nearest Neighbors: 0.8416

# Support Vector Classifier
params = {'model__C':[.1,1,10],
          'model__kernel':['rbf','poly','linear','sigmoid']}
pipe = Pipeline([('scale',CustomScaler()),('model',SVC())])
grid = GridSearchCV(pipe,param_grid=params,cv=3,n_jobs=-1,verbose=1)
grid.fit(X_train,y_train)
print 'Best params for SVC: %s' % str(grid.best_params_)
# Intialize a new SVC with the optimal parameters
svc = SVC(C=10,kernel='rbf')
accuracy_score(y_test,predictions)
evaluate_model(scv,'Support Vector Classifier')
# Accuracy for Support Vector Classifier: 0.8639

# Random Forest Classifier
params = {'model__n_estimators':[5,10,15,20,25,30,35],
          'model__criterion':['gini','entropy'],
          'model__max_depth':[5,10,25,40,50,70,None],
          'model__min_samples_split':[1,2,3,5,7,10,15]}
pipe = Pipeline([('scale',CustomScaler()),('model',RandomForestClassifier())])
grid = GridSearchCV(pipe,param_grid=params,cv=3,n_jobs=-1,verbose=1)
grid.fit(X_train,y_train)
print 'Best params for Random Forest: %s' % str(grid.best_params_)
# Intialize a new RandomForestClassifier with the optimal parameters
rfc = RandomForestClassifier(criterion='gini',max_depth=40,
                             min_samples_split=2,n_estimators=35)
evaluate_model(rfc,'Random Forest')
# Accuracy for Random Forest: 0.8428

# AdaBoost Classifier
params = {'model__n_estimators':[25,50,75],'model__learning_rate':[.1,1.,2.]}
pipe = Pipeline([('scale',CustomScaler()),('model',AdaBoostClassifier())])
grid = GridSearchCV(pipe,param_grid=params,cv=3,n_jobs=-1,verbose=1)
grid.fit(X_train,y_train)
print 'Best params for AdaBoost: %s' % str(grid.best_params_)
# Intialize a new AdaBoostClassifier with the optimal parameters
ada = AdaBoostClassifier(n_estimators=25)
evaluate_model(ada,'AdaBoost')
# Accuracy for AdaBoost: 0.7839

# Gradient Boosting Classifier
params = {'model__max_depth':[2,3,5]}
pipe = Pipeline([('scale',CustomScaler()),('model',GradientBoostingClassifier())])
grid = GridSearchCV(pipe,param_grid=params,cv=3,n_jobs=-1,verbose=1)
grid.fit(X_train,y_train)
print 'Best params for Gradient Boosting: %s' % str(grid.best_params_)
# Intialize a new GradientBoostingClassifier with the optimal parameters
gbc = GradientBoostingClassifier(max_depth=5)
evaluate_model(gbc,'Gradient Boosting')
# Accuracy for Gradient Boosting: 0.8439

# Voting Classifier
clf1 = KNeighborsClassifier(n_neighbors=10,p=1,weights='uniform')
clf2 = RandomForestClassifier(criterion='gini',max_depth=40,
                             min_samples_split=2,n_estimators=35)
clf3 = SVC(C=10,kernel='rbf',probability=True)
clf4 = GradientBoostingClassifier(max_depth=5)
eclf = VotingClassifier(estimators=[('knn',clf1),('rfc',clf2),('svc',clf3),
                                    ('gbc',clf4)],
                        voting='soft')
evaluate_model(eclf,'Voting Classifier')
# Accuracy for Voting Classifier: 0.8468
