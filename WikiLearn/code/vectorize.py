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
import numpy as np                          # numpy dependency
np.random.seed(0)
np.set_printoptions(suppress=True)

from gensim.models import Doc2Vec           # doc2vec model
from gensim.models.ldamodel import LdaModel # LDA model
from gensim import corpora
from gensim import utils

#                            Local imports
#-----------------------------------------------------------------------------#
from read import doc_corpus
from read import bag_corpus

#                           LDA encoder
#-----------------------------------------------------------------------------#

class LDA(object):
    '''
    LDA method
    '''

    def __init__(self, model_name, save_dir, path_to_docs, path_to_dictionary):

        self.docs = bag_corpus(path_to_docs, path_to_dictionary)
        self.word_map = self.docs.get_word_map()

        self.name = model_name
        self.save_dir = save_dir
        if os.path.exists('{0}/{1}/LDA'.format(self.save_dir, self.name)):
            retrain = raw_input("\t'%s' exists. Retrain? y/N: " % self.name)
            if retrain.lower() == 'n' or retrain == '':
                self.load()
                return
        self.build()
        self.train()
        self.save()
        #for bag in bags:
        #    print(encoder.encode_bag(bag))

    def __iter__(self):
        print("\tRunning model on documents...")
        num = self.docs.instances
        for i, doc in enumerate(self.docs):
            if not i % (num//100):
                print('\t\t%0.1f%% done' % round(i*100.0/num,1))
            if i > num:
                break
            yield self.encode_doc(doc)

    # User Interfaces: None yet!

    # Model I/O

    def build(self, features=300):
        print("\tBuilding LDA model...")
        self.features = features

    def train(self, epochs=5):
        '''For Wikipedia, use at least 5k-10k topics
        Memory Considerations: 8 bytes * num_terms * num_topics * 3'''
        print("\tTraining LDA model...")

        self.model = LdaModel(corpus=self.docs, num_topics=self.features, id2word=self.word_map, passes=epochs)

    def save(self):
        print("\tSaving LDA model...")
        if not os.path.exists(self.save_dir+'/'+self.name+'/LDA'):
            os.makedirs(self.save_dir+'/'+self.name+'/LDA')
        self.model.save('{0}/{1}/LDA/{1}.model'.format(self.save_dir, self.name))

    def load(self):
        print("\tLoading LDA model...")
        self.model = LdaModel.load('{0}/{1}/LDA/{1}.model'.format(self.save_dir, self.name))
        self.features = self.model.num_topics

    def get_topics(self, words=20):
        '''Returns all topics'''
        topics = self.model.show_topics(num_topics=-1,num_words=words,formatted=False)
        terms  = [y[0] for x in topics for y in x[1]]
        return [terms[i:i + words] for i in xrange(0, len(terms), words)]

    # Model methods

    # Encode/decode at word, words, and doc level

    def encode_doc(self, doc):
        return np.array([x[1] for x in self.model.get_document_topics(doc, minimum_probability=0.0)])

#                           Doc2vec encoder
#-----------------------------------------------------------------------------#

class doc2vec(object):
    '''
    doc2vec method
    '''

    def __init__(self, model_name, save_dir, path_to_docs):
        print('Initializing text encoder...')

        self.docs = doc_corpus(path_to_docs)

        self.name = model_name
        self.save_dir = save_dir
        if os.path.exists('{0}/{1}/word2vec'.format(self.save_dir, self.name)):
            retrain = raw_input("\t'%s' exists. Retrain? y/N: " % self.name)
            if retrain.lower() == 'n' or retrain == '':
                self.load()
        else:
            self.build()
            self.train()
            self.save()
        #for bag in bags:
        #    print(encoder.encode_bag(bag))

    # User Interfaces

    def nearest(self):
    
        print('\nInterface for finding nearest words')
        while True:
            sentence = raw_input("\nEnter a list of words:\n")
            if not sentence:
                return
            try:
                print(' '.join(self.get_nearest(sentence)))
            except ValueError:
                print('None of the words occur!')
            
    def outlier(self):
    
        print('\nInterface for finding outlier word')
        while True:
            sentence = raw_input("\nEnter a list of words:\n")
            if not sentence:
                return
            try:
                print(self.get_outlier(sentence))
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
                analogy = self.get_analogy(w,x,y)
                print(' '.join(analogy))
            except:
                print('Not all of the words occur!')

    # Model I/O

    def build(self, features=600):
        print("\tBuilding doc2vec model...")
        context_window=8

        self.features = features
        self.model = Doc2Vec(min_count=10, size=features, window=context_window, sample=1e-5, negative=5, workers=3)

    def train(self, epochs=30):
        print("\tTraining doc2vec model...")

        # Main Training Method
        self.model.build_vocab(self.docs)

        times = []
        for i in xrange(epochs):
            start = time.time()
            
            print("\t\tEpoch %s" % (i+1))
            self.model.train(self.docs)
            
            times.append(time.time()-start)
            remaining = sum(times)*(epochs-i-1)/len(times)/60
            print('\t\t%0.1f minutes remaining...\n' % remaining)
        #self.model.init_sims(replace=True)
        
    def save(self):
        print("\tSaving doc2vec model...")
        if not os.path.exists(self.save_dir+'/'+self.name+'/word2vec'):
            os.makedirs(self.save_dir+'/'+self.name+'/word2vec')
        self.model.save('{0}/{1}/word2vec/{1}.d2v'.format(self.save_dir,self.name))
    
    def load(self):
        print("\tLoading doc2vec model...")
        self.model = Doc2Vec.load('{0}/{1}/word2vec/{1}.d2v'.format(self.save_dir,self.name))
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