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
            self.accuracy, self.precision = self.train_classifier()
            #self.load_classifier()

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
        #y = self.corpus.get_doc_categories(100000)
        self.classifier = vector_classifier(self.directory)
        return self.classifier.train(X, y)

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
            if not i % (self.corpus.instances()//100):
                remaining = sum(times)*(self.corpus.instances()-i-1)/len(times)/3600
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
            self.build(features=100, context_window=50, min_count=1, sample=1e-5, negative=5)
            self.train(epochs=50)
            self.save()

            # Create classifier
            #self.train_classifier()
            #self.save_classifier()

        else:
            self.load()
            #self.accuracy, self.precision = self.train_classifier()
            #self.load_classifier()
            #self.analogy()

    def evaluate(self):
        url = 'http://download.tensorflow.org/data/questions-words.txt'
        return

    def nearest(self):
    
        print('\nInterface for finding nearest words')
        while True:
            sentence = raw_input("\nEnter a list of words:\n")
            if not sentence:
                return
            try:
                print(' '.join(self.get_nearest_word(sentence)))
            except ValueError:
                print('None of the words occur!')
            
    def outlier(self):
    
        print('\nInterface for finding outlier word')
        while True:
            sentence = raw_input("\nEnter a list of words:\n")
            if not sentence:
                return
            try:
                print(self.get_outlier_word(sentence))
            except ValueError:
                print('None of the words occur!')

    def analogy(self):
    
        print('\nInterface for solving analogies')
        while True:
            w = raw_input("\nEnter first word of analogy:\n")
            if not w:
                return
            print("is to")
            x = raw_input()
            print("as")
            y = raw_input()
            print("is to")
            try:
                analogy = self.get_word_analogy(w,x,y)
                print(' '.join(analogy))
            except:
                print('Not all of the words occur!')

    def get_nearest_doc(self, doc_id):
        return [x[0] for x in self.model.docvecs.most_similar(doc_id,topn=20)]

    #def get_nearest_doc(self, text):
    #    return [x[0] for x in self.model.docvecs.most_similar(self.encode_doc(text),topn=10)]

    def get_nearest_word(self, text):
        try:
            return [x[0] for x in self.model.most_similar(self.encode_words(text),topn=10)]
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

        print("\t\tBuilding vocab...")
        self.model.build_vocab(self.corpus)

    def train(self, epochs=10):
        print("\tTraining doc2vec model...")

        t = epoch_timer(epochs)
        for i in xrange(epochs):
            
            t.start()
            print("\t\tEpoch %s..." % (i+1))
            self.model.train(self.corpus)
            t.stop()

        elapsed  = t.get_elapsed()
        print('\tTime elapsed: %0.2f hours' % (elapsed))
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
        #y = self.corpus.get_doc_categories(100000)
        self.classifier = vector_classifier(self.directory)
        return self.classifier.train(X, y)

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
        return np.expand_dims(self.model.infer_vector(self.corpus.process(text)), axis=0)

    def encode_docs(self, limit=-1):
        if limit > 0:
            return np.vstack(self.model.docvecs)[:limit]
        else:
            return np.vstack(self.model.docvecs)