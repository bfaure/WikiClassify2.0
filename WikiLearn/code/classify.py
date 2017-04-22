#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
#                          Standard imports
#-----------------------------------------------------------------------------#
import os, itertools
import sys
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

from keras import callbacks
from keras.models import Sequential
from keras.layers import Dense,Activation,Dropout
from keras.layers import Embedding,LSTM
from keras.optimizers import SGD

DEFAULT_BATCH_SIZE = 20
DEFAULT_EPOCHS = 100

#                            Linear classifier
#-----------------------------------------------------------------------------#

def make_one_hot(y):
    one_hot = np.zeros((y.size, np.max(y)+1),dtype='bool')
    one_hot[np.arange(y.size), y] = 1 
    return one_hot

class vector_classifier_keras(object):
    def __init__(self, class_names=None, directory=None):
        self.class_names = class_names
        self.save_path=None
        if directory!=None:
            if not os.path.exists(directory):
                os.path.makedirs(directory)
                save_name = "vector_classifier_seq.h5"
                self.save_path = os.path.join(directory,save_name)

    def train_seq(self,X,y,test_ratio=0.2,epochs=None,batch_size=None,load_file=None):
        y_hot = make_one_hot(y)

        num_samples = X.shape[0]
        input_dim  = X.shape[2] 
        timesteps  = X.shape[1]
        output_dim = y_hot.shape[1]
        batch_size = DEFAULT_BATCH_SIZE if batch_size==None else batch_size

        if num_samples<batch_size: 
            print("\nAuto-resizing batch size")
            batch_size=num_samples

        epochs     = DEFAULT_EPOCHS if epochs==None else epochs

        print("\nBuilding model...")
        sys.stdout.flush()
        model = Sequential()
        #model.add(LSTM(200,  input_shape=(timesteps, input_dim),  return_sequences=False))
        model.add(LSTM(timesteps,input_shape=(timesteps, input_dim)))
        #model.add(Dropout(0.2))
        model.add(Dropout(0.3))
        #model.add(Dense(output_dim, input_dim=200, activation='softmax'))
        model.add(Dense(output_dim))
        model.add(Activation('sigmoid'))

        if load_file!=None: model.load_weights(load_file)
        cbks = [callbacks.EarlyStopping(monitor='val_loss', patience=3)]
        if self.save_path!=None:
            cbks.append(callbacks.ModelCheckpoint(filepath=self.save_path, monitor='val_loss', save_best_only=True))

        print("Compiling model...")
        sys.stdout.flush()
        model.compile(loss="binary_crossentropy", optimizer='adam',metrics=['accuracy'])

        print("Fitting model...")
        sys.stdout.flush()
        model.fit(X, y_hot, batch_size=batch_size, epochs=epochs,
                  callbacks=cbks, validation_split=0.25, shuffle=True)

        #loss, acc = model.evaluate(test_X, test_Y, batch_size, show_accuracy=True)
        #print('Test loss / test accuracy = {:.4f} / {:.4f}'.format(loss, acc))

        """
        model.add(Embedding(max_features, output_dim=256))
        model.add(LSTM(128))
        model.add(Dropout(0.5))
        model.add(Dense(1, activation='sigmoid'))

        print("Compiling model...")
        model.compile(loss='binary_crossentropy',
                      optimizer='rmsprop',
                      metrics=['accuracy'])

        print("Fitting model...")
        model.fit(x_train, y_train, batch_size=16, epochs=10)
        score = model.evaluate(x_test, y_test, batch_size=16)
        print("\nAccuracy: %0.5f" % score[1])
        """

    def train(self, X, y, test_ratio=0.2):

        y_hot = make_one_hot(y)

        print("\nBuilding model...")
        model = Sequential()
        model.add(Dense(64,activation='relu',input_dim=300))
        model.add(Dropout(0.5))
        model.add(Dense(64,activation='relu'))
        model.add(Dropout(0.5))
        model.add(Dense(3,activation='softmax')) # output layer
    
        sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
    
        print("Compiling model...")
        model.compile( loss='categorical_crossentropy',
                       optimizer=sgd,
                       metrics=['accuracy'])
        
        print("Fitting model...")
        model.fit( X, y_hot,
                   epochs=5,
                   batch_size=128)
    
        print("Evaluating model...")
        score = model.evaluate(X[:100],y_hot[:100], batch_size=100)
        print("\nAccuracy: %0.5f" % score[1])
    
class vector_classifier(object):

    def __init__(self, class_names=None, classifier_type="multiclass_logistic"):
        print("Initializing vector classifier...")
        self.classifier_type = classifier_type
        self.class_names = class_names
        
    def train(self, X, y, test_ratio=0.2):

        print("\tShuffling arrays...")
        p = np.random.permutation(X.shape[0])
        X, y = X[p], y[p]

        print("\tTraining classifier...")
        train_instances = int((1-test_ratio)*X.shape[0])

        # train on the training samples (as many cpus as avail.)
        if self.classifier_type=="multiclass":        
            y_hot = make_one_hot(y)
            self.model = OneVsRestClassifier(LogisticRegression(),n_jobs=-1).fit(X[:train_instances],y_hot[:train_instances])
        
        if self.classifier_type=="logistic":
            self.model = LogisticRegression(penalty='l2',solver='sag').fit(X[:train_instances],y[:train_instances])
        
        if self.classifier_type=="mlp":
            self.model = MLPClassifier(hidden_layer_sizes=(100,50,20,5)).fit(X[:train_instances],y[:train_instances])

        if self.classifier_type=="multiclass_logistic":
        
            y_hot = make_one_hot(y)
            layer1 = OneVsRestClassifier(LogisticRegression(),n_jobs=-1).fit(X[:train_instances],y_hot[:train_instances])
            layer1_output = layer1.predict_proba(X[:train_instances])

            layer2 = MLPClassifier(hidden_layer_sizes=(3,3)).fit(layer1_output,y[:train_instances])
            layer2_output = layer2.predict_proba(X[:train_instances])

            output_layer = LogisticRegression().fit(layer2_output,y[:train_instances])

            #self.model = LogisticRegression(OneVsRestClassifier(LogisticRegression(penalty='l2',solver='sag'),n_jobs=-1).fit(X[:train_instances],y_hot[:train_instances]))

        if self.classifier_type=="multiclass_logistic":
            l1_pred = layer1.predict_proba(X[train_instances:])
            l2_pred = layer2.predict_proba(l1_pred)
            o_pred = output_layer.predict(l2_pred)

            #m1_pred = m1.predict_proba(X[train_instances:])
            #m2_pred = m2.predict(m1_pred)

            num_correct = 0
            for p,a in zip(o_pred,y_int[train_instances:]):
                if p==a: num_correct+=1

            print("Accuracy %0.1f%%" % (100.0*float(num_correct)/float(len(m2_pred))))

            print("Plotting confusion matrix...")
            y_test = y_int[train_instances:]
            y_pred = o_pred 
            plot_confusion_matrix(y_test,y_pred,self.class_names,train_instances,normalize=True)
            return



        elif self.classifier_type=="multiclass":        
            y_hot = make_one_hot(y)
            self.scores = cross_val_score(self.model,X[train_instances:],y_hot[train_instances:],cv=5)
        else:        
            y_hot = make_one_hot(y)
            self.scores = cross_val_score(self.model,X[train_instances:],y_int[train_instances:],cv=5)
            
        # score on the testing samples 
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
        if hasattr(self,'model'): joblib.dump(self.model,directory+'/classifier.pkl') 
        else: print("no model, cant save")

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
