#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
#                          Standard imports
#-----------------------------------------------------------------------------#
import os
#                          Third-party imports
#-----------------------------------------------------------------------------#
import numpy as np                                  # numpy dependency
np.random.seed(0)
from sklearn.linear_model import LogisticRegression # classifier model
from sklearn.multiclass import OneVsRestClassifier
from sklearn.externals import joblib

#                            Linear classifier
#-----------------------------------------------------------------------------#

class vector_classifier(object):

    def __init__(self, name, save_dir, model_type):
        print("Initializing vector classifier...")
        self.name       = name
        self.save_dir   = save_dir
        self.model_type = model_type
        
    def train(self, input, target, test_ratio=0.15):

        print("\tShuffling arrays...")
        p = np.random.permutation(input.shape[0])
        input = input[p]
        target = target[p]

        print("\tTraining classifier...")
        train_instances = int((1-test_ratio)*input.shape[0])
        self.model = OneVsRestClassifier(LogisticRegression(),n_jobs=-1).fit(input[:train_instances],target[:train_instances])
        self.accuracy = self.model.score(input[train_instances:],target[train_instances:])
        print("\tClassifier accuracy: %0.2f%%" % (self.accuracy*100))

    def save(self):
        print("\tSaving classifier model...")
        if not os.path.exists(self.save_dir+'/'+self.name+'/classifier/'+self.model_type):
            os.makedirs(self.save_dir+'/'+self.name+'/classifier/'+self.model_type)
        joblib.dump(self.model,'{0}/{1}/classifier/{2}/{1}.pkl'.format(self.save_dir,self.name,self.model_type)) 

    def load(self):
        print("\tLoading classifier model...")
        self.model = joblib.load('{0}/{1}/classifier/{2}/{1}.pkl'.format(self.save_dir,self.name,self.model_type)) 

    def get_class(self, vector):
        return self.model.predict(vector)[0]

    def get_classes(self, matrix):
        return np.array([self.get_class(np.expand_dims(x,axis=0)) for x in matrix])