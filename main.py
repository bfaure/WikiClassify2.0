#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os, sys, time
from shutil import rmtree


import numpy as np

from matplotlib import pyplot as plt
from matplotlib import cm
from matplotlib import mlab as ml
from matplotlib import colors

#                            Local imports
#-----------------------------------------------------------------------------#
from WikiParse.main           import download_wikidump, parse_wikidump, text_corpus
from WikiLearn.code.vectorize import doc2vec
from WikiLearn.code.classify  import vector_classifier

from pathfinder import get_queries, astar_path

#                            Main function
#-----------------------------------------------------------------------------#

def classify_quality(encoder, directory):

    from bisect import bisect_left
    
    def get_row_id(row):
        return int(row.split("\t")[0])

    print("\nReading id_mapping.tsv...")
    mapping = open("id_mapping.tsv",'r').read().split("\n")
    rows = []
    for row in mapping:
        items = row.split("\t")
        if len(items)==2: rows.append(row)

    print("Sorting rows...")
    rows = sorted(rows,key=get_row_id)

    print("Splitting rows...")
    ids_talk = []
    ids_real = []
    for r in rows:
        items = r.split("\t")
        ids_talk.append(int(items[0]))
        ids_real.append(int(items[1]))

    print("Mapping size: %d"%len(ids_talk))

    def binary_search(query,lo=0,hi=None):
        hi = hi or len(ids_talk)
        return bisect_left(ids_talk,query,lo,hi)

    def talk_to_real_id(talk_page_id):
        return ids_real[binary_search(talk_page_id)]

    y = []
    x = []
    ids = []
    """
    classes = {"fa"   :np.array([0,0,0,0,0,0,1],dtype=bool),\
               "a"    :np.array([0,0,0,0,0,1,0],dtype=bool),\
               "ga"   :np.array([0,0,0,0,1,0,0],dtype=bool),\
               "b"    :np.array([0,0,0,1,0,0,0],dtype=bool),\
               "c"    :np.array([0,0,1,0,0,0,0],dtype=bool),\
               "start":np.array([0,1,0,0,0,0,0],dtype=bool),\
               "stub" :np.array([1,0,0,0,0,0,0],dtype=bool)}
    """
    classes = {"fa"   :np.array([0],dtype=int),\
               "a"    :np.array([1],dtype=int),\
               "ga"   :np.array([2],dtype=int),\
               "b"    :np.array([3],dtype=int),\
               "c"    :np.array([4],dtype=int),\
               "start":np.array([5],dtype=int),\
               "stub" :np.array([6],dtype=int)}

    counts  = {"fa"   :0,\
               "a"    :0,\
               "ga"   :0,\
               "b"    :0,\
               "c"    :0,\
               "start":0,\
               "stub" :0,\
               "unknown/not_in_model":0}

    num_lines = len(open("quality.tsv","r").read().split("\n"))
    sys.stdout.write('Parsing quality ')
    with open('quality.tsv','r') as f:
        i=0
        num_classified = 0
        for line in f:
            i+=1
            sys.stdout.write("\rParsing Quality (%d|%d|%d), (model|class.|tot.)" % (len(x),num_classified,num_lines))
            sys.stdout.flush()
            try:
                article_id, article_quality = line.decode('utf-8', errors='replace').strip().split('\t')

                qual_mapping = classes[article_quality]
                real_article_id = talk_to_real_id(int(article_id))
                num_classified+=1

                doc_vector = encoder.model.docvecs[int(real_article_id)] 

                x.append(doc_vector)
                y.append(qual_mapping)

                counts[article_quality]+=1
            except:
                counts["unknown/not_in_model"]+=1

    sys.stdout.write("\n")
    for key,value in counts.iteritems():
        print("\t"+key+" - "+str(value)+" entries")

    X = np.array(x)
    y = np.array(y)
    y = np.ravel(y)
    
    '''
    print('Training classifier...')
    for i in [100,500,1000,5000,10000,50000,100000,500000,1000000]:
        classifier = vector_classifier()
        t = time.time()
        classifier.train(X[:i+1], y[:i+1])
        print('Elapsed for %d: %0.2f' % (i,time.time()-t))
        classifier.save(directory)
    '''
    classifier = vector_classifier()
    classifier.train(X,y)
    classifier.save(directory)

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
    start_time = time.time()

    # command line argument to open the gui window
    if len(sys.argv)==2 and sys.argv[1] in ["-g","-gui"]:
        from interface import start_gui
        start_gui()
        return

    # if the parsed wikidump is not present in repository
    #if not os.path.isfile('text.tsv'):
    #    # download (if not already present)
    #    dump_path = download_wikidump('enwiki','WikiParse/data/corpora/enwiki/data')
    #    # parse the .xml file
    #    parse_wikidump(dump_path)

    # create dictionaries (load if already present)
    
    if os.path.isfile('text.tsv'):

        # settings for exeuction
        run_doc2vec = False
        if run_doc2vec:

            # training configuration
            n_examples      = 1200000 # number of articles to consume per epoch 
            features        = 300   # vector length
            context_window  = 8     # words to analyze on either side of current word 
            threads         = 8     # number of worker threads during training
            epochs          = 1   # maximum number of epochs
            print_epoch_acc = True  # print the accuracy after each epoch
            stop_early      = True  # cut off training if accuracy falls 
            backup          = True  # if true, model is saved after each epoch with "-backup" in filename
            phraser_dir = "WikiLearn/data/models/doc2vec/text" # where to save/load phraser from
            model_dir   = "WikiLearn/data/models/doc2vec/large" # where to save model

            # print out launch config
            print("\nSettings:    n_examples=%d | features=%d | context_window=%d | epochs=%d" % (n_examples,features,context_window,epochs))
            print("phraser_dir: %s" % phraser_dir)
            print("model_dir:   %s\n" % model_dir)

            # create corpus object to allow for text tagging/iteration
            documents = text_corpus('text.tsv', n_examples=n_examples)
            # assemble bigram/trigrams from corpus
            documents.get_phraser(phraser_dir)
            # create doc2vec object    
            encoder = doc2vec()
            # set model hyperparameters
            encoder.build(features=features,context_window=context_window,threads=threads)
            # train model on text corpus
            encoder.train(corpus=documents,epochs=epochs,directory=model_dir,test=print_epoch_acc,stop_early=stop_early,backup=backup)


        test = False
        if test:
            model_dir = "WikiLearn/data/models/old/5"
            encoder = doc2vec()
            encoder.load(model_dir)
            encoder.test(lower=True,show=True)


        train_classifier = True 
        if train_classifier:

            modl_d = "WikiLearn/data/models/old/5"
            #modl_d = "WikiLearn/data/models/doc2vec/large"
            #modl_d = "WikiLearn/data/models/doc2vec"
            #clas_d = "WikiLearn/data/models/classifier/older"
            clas_d = "WikiLearn/data/models/classifier/recent"
            clas_d = "WikiLearn/data/models/classifier/mlp_old"

            encoder = doc2vec()
            encoder.load(modl_d)

            classify_quality(encoder,clas_d)

        map_talk_to_real = False 
        if map_talk_to_real:

            import Cython
            import subprocess 
            subprocess.Popen('python setup.py build_ext --inplace',shell=True).wait()
            from helpers import map_talk_to_real_ids
            map_talk_to_real_ids("id_mapping.tsv") 

    else:
        print("text.tsv not present, could not create text dictionary")

    print("\nTotal time: %0.2f seconds" % (time.time()-start_time))

if __name__ == "__main__":
    main()


