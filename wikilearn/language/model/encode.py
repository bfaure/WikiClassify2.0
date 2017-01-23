#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os, linecache, time, math
import random
random.seed(0)
#                         Third-party imports
#-----------------------------------------------------------------------------#
import numpy as np                                  # numpy dependency
np.random.seed(0)

from gensim.models import Doc2Vec                   # doc2vec model

#                           Doc2vec encoder
#-----------------------------------------------------------------------------#

class doc_encoder(object):

    def __init__(self, docs, name='text_encoder'):
        print('Initializing text encoder...')

        self.name = name
        self.path = './language/model/encoders/%s' % self.name

        if os.path.exists(self.path):
            train = raw_input("\t'%s' exists. Retrain? y/N: " % self.name)
            if train.lower() == 'n' or train == '':
                self.load()
                return
        self.build()
        self.train(docs)
        self.save()

    # Model I/O

    def build(self, features=600):
        print("\tBuilding doc2vec model...")
        context_window=8

        self.features = features
        self.model = Doc2Vec(min_count=10, size=features, window=context_window, sample=1e-5, negative=5, workers=7)

    def train(self, data, epoch=30):
        print("\tTraining doc2vec model...")
        
        self.model.build_vocab(data)

        times = []
        for i in xrange(epoch):
            start = time.time()
            
            print("\t\tEpoch %s" % (i+1))
            self.model.train(data)
            
            times.append(time.time()-start)
            remaining = sum(times)*(epoch-i-1)/len(times)/60
            print('\t\t%0.1f minutes remaining...\n' % remaining)
        #self.model.init_sims(replace=True)
        
    def save(self):
        print("\tSaving doc2vec model...")
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        self.model.save('{0}/{1}.d2v'.format(self.path,self.name))
    
    def load(self):
        print("\tLoading doc2vec model...")
        self.model = Doc2Vec.load('{0}/{1}.d2v'.format(self.path,self.name))
        self.features = self.model.docvecs[0].shape[0]
    
    def get_vectors(self):
        return np.vstack(self.model.docvecs)
    
    # Model methods
    
    def get_nearest(self, sentence):
        tokens = sentence.split()
        return [x[0] for x in self.model.most_similar(self.encode_words(sentence),topn=len(tokens)+10) if x[0] not in tokens]
        
    def get_outlier(self, sentence):
    	return self.model.doesnt_match(sentence.split())        

    def get_analogy(self, x, y, z):
        return [x[0] for x in self.model.most_similar([self.encode_word(x),self.encode_word(y)],[self.encode_word(z)])]
    
    # Encode/decode at word, words, and doc level

    def encode_word(self, word):
        if word in self.model:
            return self.model[word]

    def decode_word(self, vec):
        return self.model.most_similar([vec],topn=1)[0][0]
        
    def get_vocab(self, data):
        words  = []
        result = []
        for word in data.get_vocab():
            encoding = self.encode_word(word)
            if encoding is not None:
                words.append(word)
                result.append(encoding)
        return words, np.vstack(result)

    def get_docs(self, data):
        result = [self.encode_doc(' '.join(doc.words)) for doc in data]
        return np.vstack(result)

    def encode_words(self, sentence):
        result = []
        for word in sentence.split():
            encoding = self.encode_word(word)
            if encoding is not None:
                result.append(encoding)
        return np.vstack(result)

    def decode_words(self, vecs):
        return ' '.join([self.decode_word(x) for x in vecs])

    def encode_doc(self, sentence):
        return np.expand_dims(self.model.infer_vector(sentence.split()), axis=0)