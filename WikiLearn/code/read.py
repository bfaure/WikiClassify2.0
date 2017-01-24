#
# Adapted from word2vec-sentements
# https://github.com/linanqiu/word2vec-sentiments
#

#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                             Standard imports
#-----------------------------------------------------------------------------#
import os, random, re
random.seed(0)

#                             Third-party imports
#-----------------------------------------------------------------------------#
from gensim import utils
from gensim import corpora
from gensim.models.doc2vec import TaggedDocument

def get_words(s):
    s = s.lower()
    s = s.replace('.', ' . ')
    s = s.replace(',', ' ,')
    s = s.replace(':', ' :')
    s = s.replace(';', ' ;')
    s = s.replace('(', '( ')
    s = s.replace(')', ' )')
    s = s.replace('-', ' - ')
    s = s.replace('"', ' "')
    s = s.replace("'", " '")
    return utils.to_unicode(s).split()

class doc_corpus(object):

    def __init__(self, documents):
        print("Initializing sources...")
        self.documents  = documents

    def __iter__(self):
        i = -1
        with open(self.documents, 'rb') as fin:
            for line in fin:
                i += 1
                yield TaggedDocument(get_words(line), [i])

    def get_vocab(self):
        print("Getting vocab...")
        vocab = set()
        for doc in self:
            for word in doc.words:
                vocab.add(word)
        return sorted(list(vocab))

class bag_corpus(object):

    def __init__(self, documents, dictionary):
        print("Initializing sources...")
        self.documents  = documents
        self.dictionary = corpora.Dictionary([open(dictionary).read().replace('\n',' ').split()])

    def __iter__(self):
        i = -1
        with open(self.documents, 'rb') as fin:
            for line in fin:
                i += 1
                yield self.dictionary.doc2bow(get_words(line))

    def get_vocab(self):
        print("Getting vocab...")
        vocab = set()
        for doc in self:
            for word in doc.words:
                vocab.add(word)
        return sorted(list(vocab))