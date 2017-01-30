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
import os, random, re
random.seed(0)

#                             Third-party imports
#-----------------------------------------------------------------------------#
from gensim import utils
from gensim import corpora
from gensim.models.doc2vec     import TaggedDocument
from gensim.models.phrases     import Phrases
from gensim.corpora.dictionary import Dictionary

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

class corpus(object):

    def __init__(self, doc_path):

        self.name = os.path.basename(doc_path)[:os.path.basename(doc_path).index('.')]
        self.save_dir = 'models'
        self.doc_path = doc_path

        if os.path.exists('{0}/{1}/dictionary'.format(self.save_dir, self.name)):
            retrain = raw_input("\t'%s' dictionary exists. Retrain? y/N: " % self.name)
            if retrain.lower() == 'n' or retrain == '':
                self.load_phrases()
                self.load_dictionary()
                return

        self.instances = sum(1 for doc in open(doc_path))
        self.train_phrases()
        self.save_phrases()
        self.train_dictionary()

    def __iter__(self):
        with open(self.doc_path, 'rb') as fin:
            for doc in fin:
                yield self.trigram[self.bigram[get_words(doc)]]

    def docs(self):
        return doc_corpus(self)

    def bags(self):
        return bag_corpus(self)

    def raw(self):
        with open(self.doc_path, 'rb') as fin:
            for doc in fin:
                yield get_words(doc)

    def train_dictionary(self):
        print("\tTraining dictionary...")
        self.dictionary = Dictionary(self, prune_at=2000000)
        self.dictionary.filter_extremes(no_below=3, no_above=0.5, keep_n=100000)
        self.save_dictionary()

    def save_dictionary(self):
        print("\tSaving dictionary...")
        self.dictionary.save_as_text('{0}/{1}/dictionary/{1}.tsv'.format(self.save_dir, self.name))

    def load_dictionary(self):
        print("\tLoading dictionary...")
        self.dictionary = Dictionary.load_from_text('{0}/{1}/dictionary/{1}.tsv'.format(self.save_dir, self.name))

    def train_phrases(self):

        print("\tTraining bigram detector...")
        self.bigram = Phrases(self.raw(), min_count=5, threshold=10, max_vocab_size=100000)

        print("\tTraining trigram detector...")
        self.trigram = Phrases(self.bigram[self.raw()], min_count=5, threshold=10, max_vocab_size=100000)

    def save_phrases(self):
        print("\tSaving gram detector...")
        self.bigram.save('{0}/{1}/dictionary/{1}_bigrams.pkl'.format(self.save_dir, self.name))
        self.trigram.save('{0}/{1}/dictionary/{1}_trigrams.pkl'.format(self.save_dir, self.name))

    def load_phrases(self):
        print("\tLoading gram detector...")
        self.bigram = Dictionary.load('{0}/{1}/dictionary/{1}_bigrams.pkl'.format(self.save_dir, self.name))
        self.trigram = Dictionary.load('{0}/{1}/dictionary/{1}_trigrams.pkl'.format(self.save_dir, self.name))

    def get_word_map(self):
        return dict((v,k) for k,v in self.dictionary.token2id.iteritems())

    def get_doc_vocab(self):
        print("Getting vocab...")
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
        for doc in self.corpus:
            yield self.corpus.dictionary.doc2bow(doc)

#                       Streamed doc2vec input
#-----------------------------------------------------------------------------#
class doc_corpus(object):

    def __init__(self, corpus):
        self.corpus = corpus

    def __iter__(self):
        for i, doc in enumerate(self.corpus):
            yield TaggedDocument(doc, [i])