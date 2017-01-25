#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os

#                            Local imports
#-----------------------------------------------------------------------------#

from code.vectorize import doc2vec
from code.vectorize import LDA

#                            Main function
#-----------------------------------------------------------------------------#

def main():

    data_dir = '../WikiParse/data/output/'

    if False:
        encoder = LDA('wiki', 'models', data_dir+'documents.txt', data_dir+'dictionary.txt')

    if False:
        encoder  = doc2vec('wiki', 'models', data_dir+'documents.txt')
        #encoder.nearest()
        #encoder.outlier()
        #encoder.analogy()

if __name__ == "__main__":
    main()