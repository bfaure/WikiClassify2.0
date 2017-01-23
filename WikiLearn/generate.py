#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os, random
random.seed(0)

#                          Third-party imports
#-----------------------------------------------------------------------------#
from keras.models import Sequential, model_from_json
from keras.layers import Dense, Activation, Dropout, LSTM
from keras.callbacks import EarlyStopping
import numpy as np                                  # numpy dependency
np.random.seed(0)

#                            Sequence generator
#-----------------------------------------------------------------------------#

class sequence_generator(object):

    def __init__(self, name, vecs=None, input_length=10, input_features=100):
        print("Initializing sequence generator...")
        self.name = name
        self.path = './quicklearn/models/generators/%s' % self.name
        self.length = input_length
        self.features = input_features
        
        if os.path.exists(self.path):
            train = raw_input("\t'%s' exists. Retrain? y/N: " % self.name)
            if train.lower() == 'n' or train == '':
                self.load(); return
                
        self.build()
        self.train(vecs)
        self.save()

    # Build model
    def build(self):
    
        print("\tBuilding Model...")
        self.model = Sequential()
        self.model.add(LSTM(self.features, return_sequences=True, input_shape=(self.length, self.features)))

    # Train model
    def train(self, sequence_list):
    
        X = []
        y = []
        for sequence in sequence_list:
            for i in range(0, sequence.shape[0]-self.length-1, self.length//2):
                X.append(sequence[i:i+self.length]); y.append(sequence[i+1:i+self.length+1])
        random.shuffle(X);       random.shuffle(y)
        X = np.array(X[:30000]); y = np.array(y[:30000])
    
        print("\tCompiling Model...")
        self.model.compile(optimizer='rmsprop', loss='mse', metrics=['accuracy'])
        
        print("\tTraining Model...")
        self.model.fit(X, y, batch_size=X.shape[0]//20, nb_epoch=100, validation_split=0.15, callbacks=[EarlyStopping(monitor='val_loss', patience=2)])
            
    # Save model
    def save(self):
    
        print("\tSaving Model...")
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        open(self.path + '/meta.json', 'w').write(self.model.to_json())
        self.model.save_weights(self.path + '/data.h5', overwrite=True)
    
    # Load model
    def load(self):
    
        print("\tLoading Model...")
        self.model = model_from_json(open(self.path + '/meta.json').read())
        self.model.load_weights(self.path + '/data.h5')
        self.model.compile(optimizer='rmsprop', loss='mse', metrics=['accuracy'])
    
    # Use model
    def run(self, X, steps=40):
    
        print(np.isnan(X).any())
    
        X = X[:self.length]
        result = []
        for i in xrange(steps):
            prediction = self.model.predict(np.expand_dims(X, axis=0))[:,-1]
            result.append(prediction)
            X = np.append(X[1:],prediction,axis=0)
        return(np.vstack(result))