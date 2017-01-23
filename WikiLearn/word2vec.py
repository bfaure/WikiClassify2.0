#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os

#                            Local imports
#-----------------------------------------------------------------------------#
from language.data.corpa   import text_corpa
from language.model.encode import doc_encoder

#                            Main function
#-----------------------------------------------------------------------------#

def nearest(encoder):

    print('\nInterface for finding nearest words')
    while True:
        sentence = raw_input("\nEnter a list of words:\n")
        if not sentence:
            return
        try:
            print(' '.join(encoder.get_nearest(sentence)))
        except ValueError:
            print('None of the words occur!')
        
def outlier(encoder):

    print('\nInterface for finding outlier word')
    while True:
        sentence = raw_input("\nEnter a list of words:\n")
        if not sentence:
            return
        try:
            print(encoder.get_outlier(sentence))
        except ValueError:
            print('None of the words occur!')

def analogy(encoder):

    print('\nInterface for solving analogies')
    while True:
        w = raw_input("\nEnter first word of analogy:\n")
        if not w:
            return
        print("is to")
        x = raw_input()
        print("as")
        y = raw_input()
        print("is to")
        try:
            analogy = encoder.get_analogy(w,x,y)
            print(' '.join(analogy))
        except:
        	print('Not all of the words occur!')

from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
def plot_vectors(vecs, titles):
    print("Plotting...")

    vecs = TSNE(n_components=2, early_exaggeration=4.0).fit_transform(vecs)
    fig = plt.figure()
    for i in xrange(len(titles)):
        plt.annotate(titles[i].replace('_','\n'), xy=(vecs[i,0],vecs[i,1]), fontsize='1', fontname='Arial', ha='center', va='center')
    plt.axis((np.min(vecs[:,0]),np.max(vecs[:,0]),np.min(vecs[:,1]),np.max(vecs[:,1])))
    plt.axis('off')
    plt.savefig('categories.png', dpi=800, bbox_inches='tight', transparent="True", pad_inches=0)

import numpy as np
import random
def main():

    docs    = text_corpa('language/data/text/')
    encoder = doc_encoder(docs, name='wiki')

    nearest(encoder)
    outlier(encoder)
    analogy(encoder)

    #names, vecs = encoder.get_vocab(docs)
    #plot_vectors(vecs, names)

if __name__ == "__main__":
    main()