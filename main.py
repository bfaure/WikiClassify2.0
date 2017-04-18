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
from WikiParse.main           import download_wikidump, parse_wikidump, text_corpus
from WikiLearn.code.vectorize import doc2vec
from WikiLearn.code.classify  import vector_classifier

from pathfinder import get_queries, astar_path

#                            Main function
#-----------------------------------------------------------------------------#

def classify_quality(encoder, directory):

    sys.stdout.write('Parsing quality... ')
    sys.stdout.flush()

    y = []
    ids = []
    classes = {"fa"   :np.array([0,0,0,0,0,0,1],dtype=bool),\
               "a"    :np.array([0,0,0,0,0,1,0],dtype=bool),\
               "ga"   :np.array([0,0,0,0,1,0,0],dtype=bool),\
               "b"    :np.array([0,0,0,1,0,0,0],dtype=bool),\
               "c"    :np.array([0,0,1,0,0,0,0],dtype=bool),\
               "start":np.array([0,1,0,0,0,0,0],dtype=bool),\
               "stub" :np.array([1,0,0,0,0,0,0],dtype=bool)}

    counts  = {"fa"   :0,\
               "a"    :0,\
               "ga"   :0,\
               "b"    :0,\
               "c"    :0,\
               "start":0,\
               "stub" :0,\
               "unknown":0}

    with open('quality.tsv') as f:
        for line in f:
            try:
                article_id, article_quality = line.strip().split('\t')
                y.append(classes[article_quality])
                ids.append(article_id)
                counts[article_quality]+=1
            except:
                counts["unknown"]+=1

    sys.stdout.write(str(len(y))+" entries\n")
    for key,value in counts.iteritems():
        print("\t"+key+" - "+str(value)+" entries")

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

def check_tsv_files(base_dir="."):
    print("Checking .tsv files for corruption...")
    all_items = os.listdir(base_dir)
    for fname in all_items:
        if os.path.isfile(fname):
            if fname.find(".tsv")!=-1:
                sys.stdout.write(fname+"... ")
                sys.stdout.flush()
                try:
                    f = open(fname,"r")
                    text = f.read()
                    sys.stdout.write("okay\n")
                except:
                    sys.stdout.write("failure\n")
                sys.stdout.flush()
    
    return text_documents,categories_documents,links_documents

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
        run_doc2vec = True
    
        if run_doc2vec:

            # training configuration
            n_examples      = 50  # number of articles to consume per epoch 
            features        = 400   # vector length
            context_window  = 8     # words to analyze on either side of current word 
            threads         = 8 #
            epochs          = 100   # maximum number of epochs
            print_epoch_acc = True  # print the accuracy after each epoch
            stop_early      = True  # cut off training if accuracy falls 
            backup          = True  # if true, model is saved after each epoch with "-backup" in filename
            phraser_dir = "WikiLearn/data/models/tokenizer/text" # where to save/load phraser from
            model_dir   = "WikiLearn/data/models/doc2vec" # where to save model

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
    else:
        print("text.tsv not present, could not create text dictionary")
    '''

    model = doc2vec()
    model.load('WikiLearn/data/models/doc2vec')
    model.test(lower=True,show=True,normalize=True)
    

    #if os.path.isfile('categories.tsv'):
    #    print("Getting categories dictionary...")
    #    categories_documents = gensim_corpus('categories.tsv',model_dir+"categories",make_phrases=False)
    #else: print("categories.tsv not present, could not create categories dictionary")
    #
    #if os.path.isfile('links.tsv'):
    #    print("Getting links dictionary...")
    #    links_documents = gensim_corpus('links.tsv',model_dir+"links",make_phrases=False)
    #else: print("links.tsv not present, could not create links dictionary")

    #encoder.load_pretrained('WikiLearn/data/models/doc2vec','google')
    #print("Model Accuracy: %0.2f%%" % (100*encoder.test()))

    # get the text, categories, and links dictionaries
    #text,categories,links = get_dictionaries()

    # train the google encoder on single epoch of text documents 
    #print("Training model on new data")
    #encoder.train(corpus=text, epochs=1)
    #print("Model Accuracy: %0.2f%%" % (100*encoder.test()))

    #encoder = None
    #classify_quality(encoder,'WikiLearn/data/models/classifier')

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
    print("\nTotal time: %0.2f seconds" % (time.time()-start_time))

if __name__ == "__main__":
    main()
