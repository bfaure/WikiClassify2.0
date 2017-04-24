#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
#                          Standard imports
#-----------------------------------------------------------------------------#
import os, itertools
import sys,time

from shutil import rmtree
from collections import Counter
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

from keras.layers import Conv1D,MaxPooling1D,Embedding
from keras.layers import Dense, Input, Flatten, Dropout, Merge
from keras.optimizers import Adadelta,RMSprop

DEFAULT_BATCH_SIZE = 1000
DEFAULT_EPOCHS = 100

#                            Linear classifier
#-----------------------------------------------------------------------------#

def make_one_hot(y):
    one_hot = np.zeros((y.size, np.max(y)+1),dtype='bool')
    one_hot[np.arange(y.size), y] = 1 
    return one_hot

def make_integers(y_dists):
    ints = []
    for i in range(y_dists.shape[0]):
        highest_idx = -1
        highest_prob = 0
        #print(y_dists[i])
        for j in range(y_dists.shape[1]):
            if y_dists[i][j]>highest_prob:
                highest_prob = y_dists[i][j]
                highest_idx = j 
        ints.append(highest_idx)
    return ints

def get_class_weights(y,classes=[0,1,2]):    
    totals = {}
    for i in range(len(classes)):
        totals[classes[i]]=0

    for i in range(y.shape[0]):
        totals[y[i]]+=1

    highest_count = -1  
    for key,val in totals.items():
        if val>highest_count:
            highest_count = val 

    for key,val in totals.items():
        if val is not 0:
            totals[key]=float(highest_count)/float(val)
        else:
            totals[key]=1.0

    return totals

class vector_classifier_keras(object):
    def __init__(self, class_names=None, directory=None, log=True, model_type="lstm"):

        if model_type not in ["lstm","cnn"]:
            print("ERROR: Invalid model_type input.")
            sys.exit(0)

        self.model_type = model_type
        self.class_names = class_names
        self.directory = directory
        if directory!=None and not os.path.exists(directory): os.makedirs(directory)
        self.model=None 
        self.highest_acc = None 

        self.pic_dir = os.path.join(directory,"%s-pics"%model_type)
        if not os.path.exists(self.pic_dir):
            os.makedirs(self.pic_dir)
        else:
            rmtree(self.pic_dir)
            os.makedirs(self.pic_dir)

        self.log_file=None 
        if log: self.log_file = open(os.path.join(self.directory,"%s-log.tsv"%model_type),"w")

    # Can be called multiple times, similar to train_seq
    def train_seq_iter(self,X,y,iteration,epoch,test_ratio=0.2,batch_size=None,load_file=None,plot=False):

        #self.log_file.write("Iteration:%d\tEpoch:%d\n"%(iteration,epoch))

        p = np.random.permutation(X.shape[0])
        X,y = X[p], y[p]

        y_hot = make_one_hot(y) # convert input to one-hot encoding

        #print("y[0]: ",y[0])
        #print("y_hot[0]: ",y_hot[0])

        num_samples = X.shape[0] # number of input samples
        input_dim  = X.shape[2] # number of elements in each wordvec
        timesteps  = X.shape[1] # length of each document 
        output_dim = y_hot.shape[1] 
        test_size = int(num_samples*test_ratio)
        train_size = num_samples-test_size

        if iteration==1 and epoch==0:
            print("Train/Test split: %d | %d"%(train_size,test_size))

        test_y_hot = y_hot[train_size:]
        test_y = y[train_size:]
        test_x = X[train_size:]

        train_x = X[0:train_size]
        train_y = y[0:train_size]
        train_y_hot = y_hot[0:train_size]

        if batch_size==None: 
            batch_size = int(3000/timesteps) # good for my amt of vram

            if batch_size<10: batch_size=4 
            elif batch_size<100: batch_size=12
            elif batch_size<1000: batch_size=128
            else: batch_size = 1024
            #print("Using batch size: %d"%batch_size)

        #batch_size=128
        batch_size=128

        if iteration==1 and epoch==0:
            print("Using batch size: %d" % batch_size)

        if num_samples<batch_size: 
            print("\nAuto-resizing batch size")
            batch_size=num_samples

        if self.model==None:
            print("Building %s model..."%self.model_type)
            sys.stdout.flush()
            if self.model_type=="lstm":
                self.model = Sequential()
                self.model.add(LSTM(int(timesteps*10),input_shape=(timesteps, input_dim)))
                self.model.add(Dropout(0.3))
                self.model.add(Dense(output_dim))
                self.model.add(Activation('sigmoid'))
                if load_file!=None: self.model.load_weights(load_file)
                print("Compiling model...")
                sys.stdout.flush()
                self.model.compile(loss="binary_crossentropy", optimizer='adam',metrics=['accuracy'])

            if self.model_type=="cnn":
                self.model = Sequential()
                self.model.add(Conv1D())


        #print("train_x shape: ",train_x.shape)
        #print("train_y shape: ",train_y.shape)
        #print("train_y_hot: ",train_y_hot.shape)
        #print("test_x shape: ",test_x.shape)
        #print("test_y shape: ",test_y.shape)
        #print("test_y_hot shape: ",test_y_hot.shape)

        #self.model.fit(train_x,train_y_hot,batch_size=batch_size,epochs=1)

        #p = np.random.permutation(train_x.shape[0])
        #train_x,train_y,train_y_hot = train_x[p],train_y[p],train_y_hot[p]
        
        num_batches = train_size/batch_size
        #num_batches=1
        #batch_size = train_size
        #num_batches = num_samples/batch_size
        start_time = time.time()
        for i in range(num_batches):

            #p = np.random.permutation(X.shape[0])
            #X, y, y_hot = X[p], y[p], y_hot[p]

            #p = np.random.permutation(train_x.shape[0])
            #train_x,train_y,train_y_hot = train_x[p],train_y[p],train_y_hot[p]

            #num_examples = [0]*output_dim
            #for i in range(output_dim):
            #    num_examples[i] = train_y.count()

            #print("train_x shape: ",train_x.shape)
            #print("train_y shape: ",train_y.shape)
            #print("train_y_hot: ",train_y_hot.shape)

            num_items = int( float(i+1)/float(num_batches)*float(30) )
            progress_string = "Epoch %d (%d/%d)" % (epoch,(i+1)*batch_size,train_size)
            while len(progress_string)<15:
                progress_string+=" "
            progress_string+="["

            for prog_index in range(30):
                if prog_index<=num_items: progress_string+="="
                else: progress_string += "."
            progress_string += "]"

            t0 = i*batch_size 
            t1 = t0+batch_size

            weights = get_class_weights(train_y[t0:t1])
            #print("\nClass weights",weights)

            #print("train_y[%d:%d] - "%(t0,t1),train_y[t0:t1])

            #self.model.train_on_batch(X[t0:t1],y_hot[t0:t1])
            #loss, acc = self.model.test_on_batch(X[t0:t1],y_hot[t0:t1])

            #loss,acc = self.model.train_on_batch(train_x[t0:t1],train_y_hot[t0:t1],class_weight=weights)
            loss,acc = self.model.train_on_batch(train_x[t0:t1],train_y_hot[t0:t1],class_weight='auto')
            #loss,acc = self.model.test_on_batch(train_x[t0:t1],train_y_hot[t0:t1])

            progress_string += " - %ds"% int(time.time()-start_time)
            progress_string += " - loss: %0.4f - acc: %0.1f%%"%(loss,100.0*acc)
            sys.stdout.write("\r%s"%progress_string)

            self.log_file.write("%0.5f\t%0.1f\n"%(loss,100.0*acc))
            self.log_file.flush()
        

        if plot:
            y_pred = make_integers(self.model.predict(test_x,batch_size=batch_size,verbose=0))
            #y_pred = self.model.predict_on_batch(test_x)
            plot_confusion_matrix(test_y,y_pred,self.class_names,10,normalize=True,save_dir=self.pic_dir,meta="Iter:%d-Epoch:%d"%(iteration,epoch))

        #sys.stdout.write("\n")
        #sys.stdout.flush()

        #print("Evaluating model...")
        #loss, acc = self.model.evaluate(text_x, test_y_hot, batch_size=batch_size, verbose=0)
        loss, acc = self.model.evaluate(test_x, test_y_hot, batch_size=batch_size, verbose=0)
        sys.stdout.write(' - val_loss: %0.4f - val_acc: %0.1f%%\n'%(loss,100.0*acc))

        if self.highest_acc==None or acc>self.highest_acc:
            self.highest_acc=acc 
            #print("Saving model...")
            self.model.save(os.path.join(self.directory,"%s-classifier_%d.h5"%(self.model_type,iteration)))
            #self.num_worse = 0
        #else:
        #    self.num_worse+=1
        #    if self.num_worse==3:
        #        print("Training canceled, accuracy fell for 3 consecutive ")

        if iteration==1 and epoch==0:
            #print("Saving model architecture...")
            s=open(os.path.join(self.directory,"%s-classifier_architecture.json"%(self.model_type)),"w")
            s.write(self.model.to_json())
            s.close()
        return loss 

    def train_seq(self,X,y,test_ratio=0.2,epochs=None,batch_size=None,load_file=None):
        y_hot = make_one_hot(y)

        num_samples = X.shape[0]
        input_dim  = X.shape[2] 
        timesteps  = X.shape[1]
        output_dim = y_hot.shape[1]

        test_size = int(num_samples*test_ratio)
        train_size = num_samples-test_size

        if batch_size==None: 
            #batch_size = int(12000/timesteps)
            batch_size = 128
            print("Using batch size: %d"%batch_size)

        if num_samples<batch_size: 
            print("\nAuto-resizing batch size")
            batch_size=num_samples

        epochs     = DEFAULT_EPOCHS if epochs==None else epochs

        print("\nBuilding model...")
        sys.stdout.flush()
        model = Sequential()
        #model.add(LSTM(200,  input_shape=(timesteps, input_dim),  return_sequences=False))
        #model.add(LSTM(timesteps,input_shape=(timesteps, input_dim)))
        model.add(LSTM(int(timesteps*1.5),input_shape=(timesteps, input_dim)))
        #model.add(Dropout(0.2))
        model.add(Dropout(0.3))
        #model.add(Dense(output_dim, input_dim=200, activation='softmax'))
        model.add(Dense(output_dim))
        model.add(Activation('sigmoid'))

        if load_file!=None: model.load_weights(load_file)
        cbks = [callbacks.EarlyStopping(monitor='val_loss', patience=3)]
        if self.directory!=None:
            print("Saving best model to %s"%self.directory)
            cbks.append(callbacks.ModelCheckpoint(filepath=os.path.join(self.directory,"classifier_best.h5"), monitor='val_loss', save_best_only=True))

        print("Compiling model...")
        sys.stdout.flush()
        model.compile(loss="binary_crossentropy", optimizer='adam',metrics=['accuracy'])

        print("Fitting model...\n")
        sys.stdout.flush()
        model.fit(X[:train_size], y_hot[:train_size], batch_size=batch_size, epochs=epochs,
                  callbacks=cbks, validation_split=0.25, shuffle=True)

        print("\nEvaluating model...")
        loss, acc = model.evaluate(X[train_size:], y_hot[train_size:], batch_size)
        print('Test loss / test accuracy = {:.4f} / {:.4f}'.format(loss, acc))

        print("Saving model...")
        model.save(os.path.join(self.directory,"classifier_final.h5"))

        print("Saving model architecture...")
        s=open(os.path.join(self.directory,"classifier_architecture.json"),"w")
        s.write(model.to_json())
        s.close()

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
    
def plot_confusion_matrix(y_test, y_pred, class_names, training_size, normalize=False, save_dir=None, meta=None):
    """
    *** ONLY WORKS FOR NON-MULTICLASS ***
    
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """

    #title='Confusion matrix (Training size:%d)' % training_size
    title='Confusion matrix'
    if meta is not None: title += " | "+meta 
    cmap=plt.cm.Blues

    #fig,ax = plt.subplots()
    #fig.suptitle(title,)

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
        
    if save_dir!=None:
        plt.savefig(os.path.join(save_dir,"prediction-heatmap-%s.png"%meta),bbox_inches='tight',dpi=100)
        plt.close()
    else:
        plt.show()
