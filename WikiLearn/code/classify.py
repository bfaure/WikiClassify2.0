#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
#                          Standard imports
#-----------------------------------------------------------------------------#
import os
#                          Third-party imports
#-----------------------------------------------------------------------------#
import numpy as np
np.random.seed(0)

from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.externals import joblib
from sklearn.model_selection import cross_val_score

#                            Linear classifier
#-----------------------------------------------------------------------------#

class vector_classifier(object):

    def __init__(self):
        print("Initializing vector classifier...")
        
    def train(self, X, y, test_ratio=0.2):

        print("\tShuffling arrays...")
        p = np.random.permutation(X.shape[0])
        X,y = X[p], y[p]

        print("\tTraining classifier...")
        train_instances = int((1-test_ratio)*X.shape[0])

        # train on the training samples (as many cpus as avail.)
        self.model  = OneVsRestClassifier(LogisticRegression(),n_jobs=-1).fit(X[:train_instances],y[:train_instances])
        
        # score on the testing samples 
        self.scores = cross_val_score(self.model,X[train_instances:],y[train_instances:],cv=5)

        print("Accuracy: %0.1f%% (+/- %0.1f%%)" % (100*self.scores.mean(), 100*self.scores.std()*2))
        return self.scores.mean(), self.scores.std()*2

    def save(self, directory):
        print("\tSaving classifier model...")
        if not os.path.exists(directory):
            os.makedirs(directory)
        joblib.dump(self.model,directory+'/classifier.pkl') 

    def load(self):
        print("\tLoading classifier model...")
        self.model = joblib.load(self.path) 

    def get_class(self, vector):
        return self.model.predict(vector)[0]

    def get_classes(self, matrix):
        return np.array([self.get_class(np.expand_dims(x,axis=0)) for x in matrix])