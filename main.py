#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os, sys, time
from shutil import rmtree

#                          Search Related imports
#-----------------------------------------------------------------------------#
from time import time
import heapq, codecs
from difflib import SequenceMatcher
import numpy as np
import math

#                            Local imports
#-----------------------------------------------------------------------------#
from WikiParse.main           import download_wikidump, parse_wikidump, gensim_corpus
from WikiLearn.code.vectorize import word2vec

from pathfinder import get_queries, astar_path

#                            Main function
#-----------------------------------------------------------------------------#

def get_encoder():
    encoder_directory = 'WikiLearn/data/models/word2vec'
    encoder = word2vec()
    encoder.load_pretrained(encoder_directory)
    #print("Model Accuracy: %0.2f%%" % (100*encoder.test()))
    return encoder

def main():

    if len(sys.argv)==2 and sys.argv[1] in ["-g","-gui"]:
        from interface import start_gui
        start_gui()
        return

    dump_path = download_wikidump('enwiki','WikiParse/data/corpora/enwiki/data')
    parse_wikidump(dump_path)
    encoder = get_encoder()

    while True:
        algo = raw_input("\nSelect an activity:\nPath [P]\nJoin [j]\n> ")#\na: add\n> ")
        if algo.lower() in ["p",""]:
            algo = 'p'
            break
        elif algo.lower() in ["j"]:
            break
    if algo == 'p':
        while True:
            queries = get_queries(encoder,n=2)
            if queries:
                path = astar_path(queries[0],queries[1],encoder)
                if all([i.isdigit() for i in path]):
                    for item in path:
                        print(doc_ids[item])
                else:
                    for item in path:
                        print(item)
                print('='*41)
    elif algo == 'j':
        while True:
            queries = get_queries(encoder)
            try:
                middle_word = encoder.model.most_similar(queries,topn=1)[0][0]
                print((' '*64)+'\r',end='\r')
                print('\n'+('='*41))
                #print(" + ".join([doc_ids[q] for q in queries])+" = "+doc_ids[middle_word]+"\n")
                print(" + ".join(q for q in queries)+" = "+middle_word)
                print('='*41)
            except:
                print('One of the words does not occur!')
    #elif algo.lower() in ["add"]:
    #    word_algebra(encoder)

if __name__ == "__main__":
    main()
