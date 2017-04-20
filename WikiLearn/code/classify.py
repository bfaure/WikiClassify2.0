#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
#                          Standard imports
#-----------------------------------------------------------------------------#
import os, itertools

#                          Third-party imports
#-----------------------------------------------------------------------------#
import numpy as np
np.random.seed(0)

from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.multiclass import OneVsRestClassifier
from sklearn.externals import joblib
from sklearn.model_selection import cross_val_score
from sklearn.metrics import confusion_matrix

from matplotlib import pyplot as plt
from matplotlib import cm
from matplotlib import mlab as ml
from matplotlib import colors

#                            Linear classifier
#-----------------------------------------------------------------------------#

class vector_classifier(object):

    def __init__(self, class_names=None, classifier_type="multiclass_logistic"):
        self.classifier_type = classifier_type
        self.class_names = class_names
        print("Initializing vector classifier...")
        
    def train(self, X, y, test_ratio=0.2):

        print("\tShuffling arrays...")
        p = np.random.permutation(X.shape[0])
        X,y = X[p], y[p]

        print("\tTraining classifier...")
        train_instances = int((1-test_ratio)*X.shape[0])

        # train on the training samples (as many cpus as avail.)
        if self.classifier_type=="multiclass":
            self.model = OneVsRestClassifier(LogisticRegression(),n_jobs=-1).fit(X[:train_instances],y[:train_instances])
        
        if self.classifier_type=="logistic":
            self.model = LogisticRegression(penalty='l2',solver='sag').fit(X[:train_instances],y[:train_instances])
        
        if self.classifier_type=="mlp":
            self.model = MLPClassifier(hidden_layer_sizes=(100,50,20,5)).fit(X[:train_instances],y[:train_instances])

        if self.classifier_type=="multiclass_logistic":
            self.model = LogisticRegression(OneVsRestClassifier(LogisticRegression(penalty='l2',solver='sag'),n_jobs=-1).fit(X[:train_instances],y[:train_instances]))

        # score on the testing samples 
        self.scores = cross_val_score(self.model,X[train_instances:],y[train_instances:],cv=5)
        print("Accuracy: %0.1f%% (+/- %0.1f%%)" % (100*self.scores.mean(), 100*self.scores.std()*2))

        if self.class_names!=None and self.classifier_type!="multiclass":
            print("Plotting confusion matrix...")
            y_test = y[train_instances:]
            y_pred = self.model.predict(X[train_instances:])
            plot_confusion_matrix(y_test,y_pred,self.class_names,train_instances,normalize=True)

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
    
def plot_confusion_matrix(y_test, y_pred, class_names, training_size, normalize=False):
    """
    *** ONLY WORKS FOR NON-MULTICLASS ***
    
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """

    title='Confusion matrix (Training size:%d)' % training_size
    cmap=plt.cm.Blues

    # Compute confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    
    # Plot normalized confusion matrix
    plt.figure(figsize=(10,10),dpi=120)

    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(class_names))
    plt.xticks(tick_marks, class_names, rotation=45)
    plt.yticks(tick_marks, class_names)

    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j,i,cm[i, j],horizontalalignment="center",color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.show()
