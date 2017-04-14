#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os, sys, time
from shutil import rmtree


import numpy as np

#                            Local imports
#-----------------------------------------------------------------------------#
from WikiParse.main           import download_wikidump, parse_wikidump, gensim_corpus
from WikiLearn.code.vectorize import doc2vec
from WikiLearn.code.classify  import vector_classifier

from pathfinder import get_queries, astar_path

#                            Main function
#-----------------------------------------------------------------------------#

def get_encoder(tsv_path, make_phrases, directory, features, context_window, min_count, negative, epochs):
    encoder = doc2vec()
    if not os.path.isfile(os.path.join(directory,'doc2vec.d2v')):
        encoder.build(features, context_window, min_count, negative)
        documents  = gensim_corpus(tsv_path,directory,make_phrases)
        encoder.train(documents, epochs)
        encoder.save(directory)
    else:
        encoder.load(directory)
    return encoder

def classify_quality(encoder, directory):

    print('Parsing quality...')
    y = []
    ids = []
    classes = {"fa":np.array([0,0,0,0,0,0,1],dtype=bool),\
               "a":np.array([0,0,0,0,0,1,0],dtype=bool),\
               "ga":np.array([0,0,0,0,1,0,0],dtype=bool),\
               "b":np.array([0,0,0,1,0,0,0],dtype=bool),\
               "c":np.array([0,0,1,0,0,0,0],dtype=bool),\
               "start":np.array([0,1,0,0,0,0,0],dtype=bool),\
               "stub":np.array([1,0,0,0,0,0,0],dtype=bool)}

    with open('quality.tsv') as f:
        for line in f:
            try:
                article_id, article_quality = line.strip().split('\t')
                y.append(classes[article_quality])
                ids.append(article_id)
            except:
                pass

    y = np.array(y)

    print('Parsing vectors...')
    X = np.random.randn(y.shape[0],100)

    print('Training classifier...')
    for i in [100,500,1000,5000,10000,50000,100000,500000,1000000]:
        classifier = vector_classifier()
        t = time.time()
        classifier.train(X[:i+1], y[:i+1])
        print('Elapsed for %d: %0.2f' % (i,time.time()-t))
        #classifier.save(directory)

'''
def classify_importance(encoder):
    importance = []
    importance_ids = []
    print('Parsing importance...')
    with open('importance.tsv') as f:
        for line in f:
            try:
                article_id, article_importance = line.strip().split('\t')
                try:
                    article_classes[article_id]['importance'] = article_importance
                except:
                    article_classes[article_id] = {}
                    article_classes[article_id]['importance'] = article_importance
            except:
                pass
    for article_id in article_classes.keys():
        if 'quality' not in article_classes[article_id].keys():
            article_classes[article_id]['quality'] = 'unknown'
        if 'importance' not in article_classes[article_id].keys():
            article_classes[article_id]['importance'] = 'unknown'

    print(article_classes)

    X = encoder.get_all_docvecs()
    y = 
'''

def main():

    # command line argument to open the gui window
    if len(sys.argv)==2 and sys.argv[1] in ["-g","-gui"]:
        from interface import start_gui
        start_gui()
        return

    # if the parsed wikidump is not present in repository
    if not os.path.isfile('text.tsv'):
        dump_path = download_wikidump('enwiki','WikiParse/data/corpora/enwiki/data')
        parse_wikidump(dump_path)

    #encoder = doc2vec()
    #encoder.load_pretrained('WikiLearn/data/models/doc2vec','google')
    #print("Model Accuracy: %0.2f%%" % (100*encoder.test()))

    encoder = None
    classify_quality(encoder,'WikiLearn/data/models/classifier')

    '''
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
    '''

if __name__ == "__main__":
    main()
