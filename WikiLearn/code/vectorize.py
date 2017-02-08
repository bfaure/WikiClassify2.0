#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os, re, time, math
import random
random.seed(0)

#                         Third-party imports
#-----------------------------------------------------------------------------#

import numpy as np
np.random.seed(0)

from gensim.models.ldamodel import LdaModel
from gensim.models import Doc2Vec
from gensim import corpora
from gensim import utils

#                            Local imports
#-----------------------------------------------------------------------------#

from classify import vector_classifier
from evaluate import evaluate

#-----------------------------------------------------------------------------#
def check_directory(directory):
    if not os.path.isdir(directory):
        print("\t\tCreating directory...")
        os.makedirs(directory)
        return False
    return True

#                             LDA encoder
#-----------------------------------------------------------------------------#

class LDA(object):

    def __init__(self, corpus, directory):
        print("Initializing LDA model...")

        self.corpus    = corpus
        self.directory = directory

        if not os.path.exists(self.directory):

            # Create main model
            self.build(features=5000)
            self.train(epochs=1)
            self.save()

            # Create classifier
            self.train_classifier()
            self.save_classifier()

        else:
            self.load()
            self.load_classifier()

    # Model I/O

    def build(self, features=5000):
        print("\tBuilding LDA model...")
        self.features = features

    def train(self, epochs=1):
        '''For Wikipedia, use at least 5k-10k topics
        Memory Considerations: 8 bytes * num_terms * num_topics * 3'''
        print("\tTraining LDA model...")
        self.model = LdaModel(corpus=self.corpus.bags, num_topics=self.features, id2word=self.corpus.get_word_map(), passes=epochs)

    def save(self):
        print("\tSaving LDA model...")
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        self.model.save(self.directory+'/LDA.model')

    def load(self):
        print("\tLoading LDA model...")
        self.model = LdaModel.load(self.directory+'/LDA.model')
        self.features = self.model.num_topics

    def get_topics(self, words=20):
        '''Returns all topics'''
        topics = self.model.show_topics(num_topics=-1,num_words=words,formatted=False)
        terms  = [y[0] for x in topics for y in x[1]]
        return [terms[i:i+words] for i in xrange(0,len(terms),words)]

    def train_classifier(self):
        X = self.encode_docs(100000)
        y = self.corpus.get_doc_categories(100000)
        self.classifier = vector_classifier(self.directory)
        self.classifier.train(X, y)
        y_pred = self.classifier.get_classes(X)
        evaluate(y, y_pred, self.corpus.get_category_names())

    def save_classifier(self):
        self.classifier.save()

    def load_classifier(self):
        self.classifier = vector_classifier(self.directory).load()

    # Model methods

    def encode_doc(self, doc):
        return np.array([x[1] for x in self.model.get_document_topics(doc, minimum_probability=0.0)])

    def encode_docs(self, limit=-1):
        print("\tEncoding documents...")
        vecs = []
        times = []
        for i, doc in enumerate(self.corpus.bags):
            start = time.time()
            vecs.append(self.encode_doc(doc))
            if i == limit:
                break

            # Progress
            times.append(time.time()-start)
            if not i % (self.corpus.docs.instances()//100):
                remaining = sum(times)*(self.corpus.docs.instances()-i-1)/len(times)/3600
                print('\t\t%0.2f hours remaining...\n' % remaining)
                times = times[-10000:]

        return np.array(vecs)

#                           Doc2vec encoder
#-----------------------------------------------------------------------------#

class doc2vec(object):

    def __init__(self, corpus, directory):
        print('Initializing doc2vec encoder...')
        self.corpus    = corpus
        self.directory = directory

        if not os.path.exists(self.directory):

            # Create main model
            self.build(features=400, context_window=8, min_count=3, sample=1e-5, negative=5)
            self.train(epochs=10)
            self.save()

            # Create classifier
            self.train_classifier()
            self.save_classifier()

        else:
            self.load()
            self.load_classifier()

    # Model I/O

    def build(self, features=400, context_window=8, min_count=3, sample=1e-5, negative=5):
        print("\tBuilding doc2vec model...")

        self.features = features
        self.model = Doc2Vec(min_count=min_count, size=features, window=context_window, sample=sample, negative=negative, workers=8)

    def train(self, epochs=10):
        print("\tTraining doc2vec model...")

        # Main Training Method
        self.model.build_vocab(self.corpus.docs)

        times = []
        for i in xrange(epochs):
            start = time.time()
            
            print("\t\tEpoch %s" % (i+1))
            self.model.train(self.corpus.docs)
            
            times.append(time.time()-start)
            remaining = sum(times)*(epochs-i-1)/len(times)/3600
            print('\t\t%0.2f hours remaining...\n' % remaining)
        #self.model.init_sims(replace=True)
        
    def save(self):
        print("\tSaving doc2vec model...")
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        self.model.save(self.directory+'/word2vec.d2v')
    
    def load(self):
        print("\tLoading doc2vec model...")
        self.model = Doc2Vec.load(self.directory+'/word2vec.d2v')
        self.features = self.model.docvecs[0].shape[0]
    
    def train_classifier(self):
        X = self.encode_docs(100000)
        y = self.corpus.get_doc_categories(100000)
        self.classifier = vector_classifier(self.directory)
        self.classifier.train(X, y)
        y_pred = self.classifier.get_classes(X)
        evaluate(y, y_pred, self.corpus.get_category_names())

    def save_classifier(self):
        self.classifier.save()

    def load_classifier(self):
        self.classifier = vector_classifier(self.directory).load()
    
    # Encode/decode at word, words, and doc level

    def encode_word(self, word):
        if word in self.model:
            return self.model[word]

    def decode_word(self, vec):
        return self.model.most_similar([vec],topn=1)[0][0]

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

    def encode_docs(self, limit=-1):
        if limit > 0:
            return np.vstack(self.model.docvecs)[:limit]
        else:
            return np.vstack(self.model.docvecs)