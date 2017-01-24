#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os

#                            Local imports
#-----------------------------------------------------------------------------#
from code.read      import text_corpa
from code.vectorize import doc_encoder
from code.visualize import plot_vectors

#                            Main function
#-----------------------------------------------------------------------------#

def main():

    encoder = doc_encoder('wiki')
    docs    = text_corpa('../WikiParse/data/output/')
    encoder.train(docs, 'models')

    encoder.nearest()
    encoder.outlier()
    encoder.analogy()

    #names, vecs = encoder.get_vocab(docs)
    #plot_vectors(vecs[:100], names[:100])

if __name__ == "__main__":
    main()