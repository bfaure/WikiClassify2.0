#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os, time, datetime, sys, gzip, requests
import random
random.seed(0)

from urlparse import urlparse

#                         Third-party imports
#-----------------------------------------------------------------------------#

import numpy as np
np.random.seed(0)

from gensim.models.ldamodel import LdaModel
from gensim.models import Doc2Vec
from gensim.models import Word2Vec
from gensim.models.keyedvectors import KeyedVectors

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

def download(url, directory, show=True):
    if not os.path.isdir(directory): os.makedirs(directory)
    file_name = os.path.basename(urlparse(url)[2])
    file_path = os.path.join(directory, file_name)
    if show: sys.stdout.write("\tDownloading '%s'... " % file_name)
    if not os.path.isfile(file_path):
        try:
            with open(file_path, "wb") as f:
                response = requests.get(url, stream=True)
                total_length = response.headers.get('content-length')
                megabytes = int(total_length)/1000000
                if show: sys.stdout.write(str(megabytes)+" MB\n")

                if total_length is not None:
                    dl = 0
                    total_length = int(total_length)
                    for data in response.iter_content(chunk_size=4096):
                        dl += len(data)
                        f.write(data)
                        num_items = int( float(dl)/float(total_length)*float(25) )
                        progress_string = ""
                        for prog_index in range(25):
                            if prog_index<=num_items: progress_string+="-"
                            else: progress_string += " "
                        if show: sys.stdout.write("\r\t\t["+progress_string+"] "+str(100.0*dl/total_length)[:4]+"% done")
                        if show: sys.stdout.flush()
                    if show: sys.stdout.write("\n")
                else:
                    f.write(response.content)
        except:
            print("\t\tCould not download '%s'." % file_name)
    else:
        if show: print("\n\t\t'%s' already exists." % file_name)
    return file_path

def expand_gz(directory):
    print("\tExpanding gz... ")
    #if not os.path.isfile(file_path[:-3]):
    for file_path in os.listdir(directory):
        file_path = directory+"/"+file_path
        if file_path.endswith(".gz"):
            if not os.path.isfile(file_path[:-3]):
                try:
                    with gzip.open(file_path) as src:
                        with open(file_path[:-3], 'wb') as new_file:
                            new_file.write(src.read())
                except:
                    print("\t\tCould not expand file %s"%file_path)

            return file_path[:-3]
    #else:
    #    print("\t\tFile already expanded.")
    print("No gz files in directory.")

def lowerize(directory, path):
    if directory[-1]!="/": directory+="/"
    file = path.split("/")[-1]
    new_file = file.split(".")[0]+"-lower.txt"
    if os.path.exists(directory+new_file): return directory+new_file
    f = open(path,"r")
    text = f.read()
    new_text = text.lower()
    f.close()
    new_f = open(directory+new_file,"w")
    new_f.write(new_text)
    new_f.close()
    return directory+new_file

#                             LDA encoder ** Untested w/ current updates
#-----------------------------------------------------------------------------#

class LDA(object):

    def __init__(self, corpus, directory):
        print("Initializing LDA model...")

        self.corpus    = corpus
        self.directory = directory
        '''
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
            '''

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
        if not os.path.exists(self.directory): os.makedirs(self.directory)
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

    def __init__(self):
        print('Initializing doc2vec encoder...')
        pass

    def get_all_docvecs():
        return np.array(self.model.docvecs)

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

    def build(self, features=400, context_window=8, min_count=3, sample=1e-5, negative=5, threads=7):
        print("\tBuilding doc2vec model...")

        self.features = features
        self.model = Doc2Vec(min_count=min_count, size=features, window=context_window, sample=sample, negative=negative, workers=threads)

    def train(self, corpus, epochs=10, directory=None, test=False, stop_early=True):
        if directory!=None and directory[-1]!='/': directory+='/'

        # calcualte the effective size of training corpus given the skip_rate probability
        #eff_size = corpus.document_size*corpus.skip_rate 
        #print("\tEffective corpus size: %d MB" % int(eff_size/1000000))

        # linear best fit line from wolfram alpha
        #pred_epoch_time = (3.94749*(10**-6)*eff_size)+125.886 
        #print("\tPredicted epoch time:  %0.1f sec" % pred_epoch_time)

        t_e = time.time()
        sys.stdout.write("\t\tBuilding vocab... ")
        sys.stdout.flush()
        self.model.build_vocab(corpus)
        sys.stdout.write("%0.1f sec\n" % (time.time()-t_e))

        last_acc = None 
        print("\tTraining doc2vec model...")
        t = epoch_timer(epochs)
        for i in xrange(epochs):
            t.start()
            t_e = time.time()
            sys.stdout.write("\t\tEpoch %d... " % (i+1))
            sys.stdout.flush()
            self.model.train(corpus)
            sys.stdout.write("%0.1f sec\n" % (time.time()-t_e))
            t.stop()

            if test or stop_early: acc = self.test(lower=True,show=False)
            if test: 
                print("\t\t\tModel Acc: \t%0.7f%%" % (100*acc))
                #print("\t\t\")

            if stop_early:
                if last_acc!=None and acc<last_acc: break
                last_acc = acc 

        elapsed  = t.get_elapsed()
        print('\tTime elapsed: %0.2f hours' % (elapsed))
        #self.model.init_sims(replace=True)

        if directory!=None:
            print("\tSaving doc2vec model...")
            self.model.save(directory+'/word2vec.d2v')

    def test(self,lower=False,show=True):
        if show: print("Testing model...")
        directory = "WikiLearn/data/tests/"
        url = "https://raw.githubusercontent.com/nicholas-leonard/word2vec/master/questions-words.txt"
        path = download(url,directory,show)
        if lower: path = lowerize(directory,path)
        acc = self.model.accuracy(path, case_insensitive=True)
        num_correct = sum([len(x['correct']) for x in acc])
        num_incorrect = sum([len(x['incorrect']) for x in acc])
        acc = float(num_correct)/(num_correct+num_incorrect)
        if show: print("Model Accuracy: %0.7f%%" % (100*acc))
        return acc

    def save_vocab(self, path):
        vocab = model.vocab.keys()
        with open(path, 'w+') as f:      
            for i in xrange(0, len(vocab)):
                f.write(vocab[i].encode('UTF-8') + '\n')

    def intersect_pretrained(self, directory, version='google'):
        if directory[-1]!="/": directory += "/" 

        if not hasattr(self,'model'): 
            print("You must have a trained model before calling intersect_pretrained")
            return 

        if version == 'google':
            print("Intersecting model with Google model...")
            url = "https://s3.amazonaws.com/mordecai-geo/GoogleNews-vectors-negative300.bin.gz"
            path = download(url,directory)
            path = expand_gz(directory)
            print("\tMerging...")
            self.model.intersect_word2vec_format(path,binary=True)
            print("Merged model with %s model" % version)

    def load_pretrained(self, directory, version='google'):
        if directory[-1]!="/": directory += "/" 

        if version == 'google':
            url = "https://s3.amazonaws.com/mordecai-geo/GoogleNews-vectors-negative300.bin.gz"
            path = download(url,directory)
            path = expand_gz(directory)
            #self.model = Word2Vec.load_word2vec_format(path, binary=True)
            print("Loading model...")
            self.model = KeyedVectors.load_word2vec_format(path,binary=True)
            print("Loaded pretrained %s model" % version)

    def load(self, directory):
        if directory[-1]!="/": directory += "/" 

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
