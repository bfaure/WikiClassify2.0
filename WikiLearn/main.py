#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os

#                            Local imports
#-----------------------------------------------------------------------------#

from code.read import corpus
from code.vectorize import doc2vec
from code.vectorize import LDA

#                            Main function
#-----------------------------------------------------------------------------#

def main():

    data_dir = '../WikiParse/data/output/'
    documents = corpus(data_dir+'documents.txt')
    #for doc in documents:
    #    print(doc)

    if False:
        encoder = LDA(documents, 'models')
        print(encoder.get_topics())
        #for doc in encoder:
        #    print(doc)
    
    if True:
        encoder  = doc2vec(documents, 'models')
        #encoder.nearest()
        #encoder.outlier()
        #encoder.analogy()

if __name__ == "__main__":
    main()