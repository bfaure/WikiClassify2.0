#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Third-party imports
#-----------------------------------------------------------------------------#
import numpy as np                                  # numpy dependency
np.random.seed(0)
from sklearn.linear_model import LogisticRegression # classifier model

#                            Linear classifier
#-----------------------------------------------------------------------------#

class vector_classifier(object):

    def __init__(self):
        print("Initializing vector classifier...")
        
    def train(self, input, target, class_names, test_ratio=0.15):
        print("\tTraining classifier...")
        self.class_names = class_names
        train_instances = int((1-test_ratio)*input.shape[0])
        self.model = LogisticRegression().fit(input[:train_instances], target[:train_instances])
        self.accuracy = self.model.score(input[train_instances:], target[train_instances:])
        print("\tClassifier accuracy: %0.2f%%" % (self.accuracy * 100))

    def get_class(self, vector, classes):
        return self.class_names[int(self.model.predict(vector)[0])]