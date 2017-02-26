#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os, sys, time

#                            Local imports
#-----------------------------------------------------------------------------#

from WikiParse.main           import wiki_corpus
from WikiLearn.code.vectorize import LDA, doc2vec

#                            Main function
#-----------------------------------------------------------------------------#

corpus_name   = 'simplewiki'
run_LDA       = False
run_word2vec  = True
corpus_directory   = 'WikiParse/data/corpora/%s' % corpus_name
LDA_directory      = 'WikiLearn/data/models/LDA/%s' % corpus_name
word2vec_directory = 'WikiLearn/data/models/word2vec/%s' % corpus_name
def main():
    documents = wiki_corpus(corpus_name, corpus_directory)
    if run_LDA:
        start_time = time.time()
        encoder = LDA(documents.categories, LDA_directory)
    if run_word2vec:
        start_time = time.time()
        encoder = doc2vec(documents.revision_categories, word2vec_directory)
        for doc in documents.category_names:
            catname = doc[9:].replace('_',' ')
            if catname.strip():
                nearest = encoder.get_nearest_word(doc[9:])
                if nearest:
                    print('\t'.join(nearest))

if __name__ == "__main__":
    main()