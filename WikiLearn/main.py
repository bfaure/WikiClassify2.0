#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os

#                            Local imports
#-----------------------------------------------------------------------------#
from code.read      import doc_corpus
from code.read      import bag_corpus

from code.vectorize import doc2vec
from code.vectorize import LDA

from code.visualize import plot_vectors

#                            Main function
#-----------------------------------------------------------------------------#

def main():

    data_dir = '../WikiParse/data/output/'

    docs     = doc_corpus(data_dir+'documents.txt')
    encoder  = doc2vec('wiki')
    encoder.train(docs, 'models')
    for doc in encoder.get_docs(docs):
        print(doc)

    bags     = bag_corpus(data_dir+'documents.txt', data_dir+'dictionary.txt')
    encoder  = LDA('wiki')
    encoder.train(bags, 'models')
    for bag in bags:
        print(encoder.encode_bag(bag))

    #encoder.nearest()
    #encoder.outlier()
    #encoder.analogy()

    #names, vecs = encoder.get_vocab(docs)
    #plot_vectors(vecs[:100], names[:100])

if __name__ == "__main__":
    main()