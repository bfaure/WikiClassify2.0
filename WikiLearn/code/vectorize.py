#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os, time, datetime
import random
random.seed(0)

#                         Third-party imports
#-----------------------------------------------------------------------------#

import numpy as np
np.random.seed(0)

from gensim.models.ldamodel import LdaModel
from gensim.models import Doc2Vec

#                            Local imports
#-----------------------------------------------------------------------------#

from classify import vector_classifier

#-----------------------------------------------------------------------------#
def check_directory(directory):
    if not os.path.isdir(directory):
        print("\t\tCreating directory...")
        os.makedirs(directory)
        return False
    return True

class epoch_timer(object):
    def __init__(self, epochs):
        self.epochs = epochs
        self.epoch  = -1
        self.times  = []

    def start(self):
        self.epoch += 1
        self.before =  time.time()

    def stop(self):
        after = time.time()
        self.times.append(after-self.before)
        avg_time  = sum(self.times)/len(self.times)
        remaining = avg_time*(self.epochs-self.epoch-1)
        next_time = datetime.datetime.fromtimestamp(after+avg_time).strftime('%d %b %Y %H:%M')
        eta_time  = datetime.datetime.fromtimestamp(after+remaining).strftime('%d %b %Y %H:%M')
        if self.epoch < self.epochs:
            print('\t\t\tNext epoch:\t%s' % next_time)
            print('\t\t\tETA:\t\t%s' % eta_time)

    def get_elapsed(self):
        return sum(self.times)/3600.0

#                           Doc2vec encoder
#-----------------------------------------------------------------------------#

class doc2vec(object):

    def __init__(self):
        print('Initializing doc2vec encoder...')
        pass

    def get_nearest_doc(self, doc_id):
        return [x[0] for x in self.model.docvecs.most_similar(doc_id,topn=20)]

    def get_nearest_word(self, text, topn=10):
        try:
            return [x[0] for x in self.model.most_similar(self.encode_words(text),topn=topn) if x!=text]
        except:
            return None
        
    def get_outlier_word(self, text):
        return self.model.doesnt_match(text)   

    def get_word_analogy(self, x, y, z):
        return [x[0] for x in self.model.most_similar(positive=[self.encode_word(y),self.encode_word(z)],negative=[self.encode_word(x)])]

    # Model I/O

    def build(self, features=400, context_window=8, min_count=3, sample=1e-5, negative=5):
        print("\tBuilding doc2vec model...")

        self.features = features
        self.model = Doc2Vec(min_count=min_count, size=features, window=context_window, sample=sample, negative=negative, workers=7)

    def train(self, corpus, epochs=10):

        print("\t\tBuilding vocab...")
        self.model.build_vocab(corpus)

        print("\tTraining doc2vec model...")

        t = epoch_timer(epochs)
        for i in xrange(epochs):
            
            t.start()
            print("\t\tEpoch %s..." % (i+1))
            self.model.train(corpus)
            t.stop()

        elapsed  = t.get_elapsed()
        print('\tTime elapsed: %0.2f hours' % (elapsed))
        #self.model.init_sims(replace=True)
        
    def save(self, directory):
        print("\tSaving doc2vec model...")
        self.model.save(directory+'/word2vec.d2v')
    
    def load(self, directory):
        print("\tLoading doc2vec model...")
        self.model = Doc2Vec.load(directory+'/word2vec.d2v')
        self.features = self.model.docvecs[0].shape[0]
    
    # Encode/decode at word, words, and doc level

    def encode_word(self, word):
        if word in self.model:
            return self.model[word]

    def decode_word(self, vec):
        return self.model.most_similar([vec],topn=1)[0][0]

    def encode_words(self, text):
        result = []
        for word in text.split(' '):
            encoding = self.encode_word(word)
            if encoding is not None:
                result.append(encoding)
        return np.vstack(result)

    def decode_words(self, vecs):
        return ' '.join([self.decode_word(x) for x in vecs])

    def encode_doc(self, text):
        return np.expand_dims(self.model.infer_vector(text.split(' ')), axis=0)

    def encode_docs(self, limit=-1):
        if limit > 0:
            return np.vstack(self.model.docvecs)[:limit]
        else:
            return np.vstack(self.model.docvecs)