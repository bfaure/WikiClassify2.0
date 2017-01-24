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

class text_corpa(object):

    def __init__(self, directory):
        print("Initializing sources...")
        self.directory = directory
        self.sources = [self.directory+'/'+x for x in sorted(os.listdir(self.directory)) if not x.startswith('.')]

    def __iter__(self):
        i = -1
        for source in self.sources:
            with open(source, 'rb') as fin:
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