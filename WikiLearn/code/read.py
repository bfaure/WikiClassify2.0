#
# Adapted from word2vec-sentements
# https://github.com/linanqiu/word2vec-sentiments
#

#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
reload(sys);
sys.setdefaultencoding("utf-8")

#                             Standard imports
#-----------------------------------------------------------------------------#
import os, random, re, tarfile
random.seed(0)
import json, codecs
from urllib import urlretrieve
from urlparse import urlparse

#                             Third-party imports
#-----------------------------------------------------------------------------#
import numpy as np

from gensim import utils
from gensim import corpora
from gensim.models.doc2vec     import TaggedDocument
from gensim.models.phrases     import Phrases
from gensim.corpora.dictionary import Dictionary

class corpus(object):

    def __init__(self, dataset_name, document_directory='data/documents', save_dir='data/models'):
        print("Initializing document corpus...")

        self.name          = dataset_name
        self.save_dir      = save_dir
        self.document_path = document_directory+'/'+dataset_name+'/documents.tsv'
        self.instances     = sum(1 for doc in open(self.document_path))
        self.classes       = []
        with open(document_directory+'/'+dataset_name+'/category_names.tsv') as fin:
            for line in fin:
                c_code, name = line.split('\t')
                self.classes.append((c_code, name.strip()))

    def __iter__(self):
        with open(self.document_path, 'rb') as fin:
            for i, doc in enumerate(fin):
                categories, doc = doc.split('\t')
                yield self.trigram[self.bigram[get_words(doc)]]

    def docs(self):
        return doc_corpus(self)

    def bags(self):
        return bag_corpus(self)

    def raw(self):
        with open(self.document_path, 'rb') as fin:
            for doc in fin:
                yield get_words(doc)

    def train_dictionary(self):
        print("\tTraining word list...")
        self.dictionary = Dictionary(self, prune_at=2000000)
        self.dictionary.filter_extremes(no_below=3, no_above=0.5, keep_n=100000)
        self.save_dictionary()

    def save_dictionary(self):
        print("\tSaving word list...")
        if not os.path.exists(self.save_dir+'/'+self.name+'/tokenizer'):
            os.makedirs(self.save_dir+'/'+self.name+'/tokenizer')
        self.dictionary.save_as_text(self.save_dir+'/'+self.name+'/tokenizer/word_list.tsv')

    def load_dictionary(self):
        print("\tLoading word list...")
        self.dictionary = Dictionary.load_from_text(self.save_dir+'/'+self.name+'/tokenizer/word_list.tsv')

    def train_phrases(self):

        print("\tTraining bigram detector...")
        self.bigram = Phrases(self.raw(), min_count=5, threshold=10, max_vocab_size=100000)

        print("\tTraining trigram detector...")
        self.trigram = Phrases(self.bigram[self.raw()], min_count=5, threshold=10, max_vocab_size=100000)

    def save_phrases(self):
        print("\tSaving gram detector...")
        self.bigram.save(self.save_dir+'/'+self.name+'/tokenizer/bigrams.pkl')
        self.trigram.save(self.save_dir+'/'+self.name+'/tokenizer/trigrams.pkl')

    def load_phrases(self):
        print("\tLoading gram detector...")
        self.bigram = Dictionary.load(self.save_dir+'/'+self.name+'/tokenizer/bigrams.pkl')
        self.trigram = Dictionary.load(self.save_dir+'/'+self.name+'/tokenizer/trigrams.pkl')

    def get_classes(self):
        print("\tLoading classes...")

        classes = []
        with open(self.document_path, 'rb') as fin:
            for i, doc in enumerate(fin):
                categories, doc = doc.split('\t')
                classes.append([int(x) for x in categories.split(',')])
            #for doc in fin:
            #    categories, doc = doc.split('\t')
            #    classes.append([int(x) for x in categories.split(',')])
        return np.array(classes)

    def get_word_map(self):
        print("\tGetting word map...")
        return dict((v,k) for k,v in self.dictionary.token2id.iteritems())

    def get_doc_vocab(self):
        print("\tGetting vocab...")
        vocab = set()
        for doc in self:
            for word in doc.words:
                vocab.add(word)
        return sorted(list(vocab))

#                         Streamed LDA input
#-----------------------------------------------------------------------------#
class bag_corpus(object):

    def __init__(self, corpus):
        self.corpus  = corpus

    def __iter__(self):
        print("\t\tIterating bag of words...")
        for doc in self.corpus:
            yield self.corpus.dictionary.doc2bow(doc)

#                       Streamed doc2vec input
#-----------------------------------------------------------------------------#
class doc_corpus(object):

    def __init__(self, corpus):
        self.corpus = corpus

    def __iter__(self):
        print("\t\tIterating tagged docs...")
        for i, doc in enumerate(self.corpus):
            yield TaggedDocument(doc, [i])

def get_words(s):
    s = s.lower()
    s = s.replace('.', ' . ')
    s = s.replace(',', ' , ')
    s = s.replace(':', ' : ')
    s = s.replace(';', ' ; ')
    s = s.replace('(', ' ( ')
    s = s.replace(')', ' )')
    s = s.replace('-', ' - ')
    s = s.replace('"', ' " ')
    s = s.replace("'", " ' ")
    return utils.to_unicode(s).split()

def download_tarball(url, dataset_directory='data/datasets'):

    if not os.path.isdir(dataset_directory):
        print("\tCreating dataset directory..." % dataset_name)
        os.mkdir(dataset_directory)
    file_name    = os.path.basename(urlparse(url)[2])
    dataset_name = file_name[:file_name.index('.')]
    directory    = dataset_directory+'/'+dataset_name
    print("Downloading %s dataset..." % dataset_name)
    if not os.path.isdir(directory):
        try:
            urlretrieve(url, dataset_directory+'/'+file_name)
            try:
                print("\tExtracting %s..." % file_name)
                os.mkdir(directory)
                tarfile.open(dataset_directory+'/'+file_name, 'r').extractall(directory)
                os.remove(dataset_directory+'/'+file_name)
            except:
                print("\tCould not extract %s tarball." % file_name)
        except:
            print("\tCould not download %s dataset." % dataset_name)
    else:
        print("\t%s dataset already exists." % dataset_name)
    return dataset_name

def parse_dataset(dataset_name, dataset_directory='data/datasets', document_directory='data/documents'):
    print("Parsing %s dataset..." % dataset_name)

    directory = document_directory+'/'+dataset_name
    if not os.path.isdir(directory):

        os.mkdir(directory)

        document_path = directory+'/'+'documents.tsv'
        document_file = open(document_path,'a+')

        # A file with one "category_id TAB category_name" per line
        category_name_path = directory+'/'+'category_names.tsv'
        category_name_file = open(category_name_path,'a+')

        # A file with one "category_id TAB parent1,parent2,..." per line
        category_tree_path = directory+'/'+'category_tree.tsv'
        category_tree_file = open(category_tree_path,'a+')

        # Method for parsing imdb dataset
        if dataset_name == 'aclImdb_v1':
            classes = ['pos','neg']
            for c_code, classification in enumerate(classes):
                category_name_file.write('%s\t%s\n' % (c_code,classification))
                for subset in ['test','train']:
                    current_directory = dataset_directory+'/'+dataset_name+'/aclImdb/'+subset+'/'+classification
                    for file_name in os.listdir(current_directory):
                        if file_name.endswith('.txt'):
                            with open(current_directory+'/'+file_name) as f:
                                doc = f.read()
                                for bad_str in ['<br />', '\n', '\t']:
                                    doc = doc.replace(bad_str, ' ')
                                document_file.write('%s\t%s\n' % (c_code, doc))

        category_name_file.close()
        document_file.close()

    else:
        print("\t%s dataset already parsed." % dataset_name)