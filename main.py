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

def check_if_in_text(a_id,text_f):
    for line in text_f:
        if int(line.split("\t")[0])==int(a_id): return True 
    return False

title_map = open('titles.tsv','r').read().split("\n")
def title_to_id(title):
    i=-1
    for l in title_map:
        i+=1
        if l.split("\t")[1].lower()==title.lower():
            del title_map[i]
            return l.split("\t")[0]
    return "None"

def id_to_title(id):
    i=-1
    for l in title_map:
        i+=1
        if str(l.split("\t")[0].lower())==(str(id).lower()):
            del title_map[i]
            return l.split("\t")[1]
    return "None"

quality_map = open('quality.tsv','r').read().split("\n")
def id_to_quality(id):
    i=-1
    for l in quality_map:
        i+=1
        if str(l.split("\t")[0].lower())==(str(id).lower()):
            del quality_map[i]
            return l.split("\t")[1]
    return "None"

def talk_to_real_id(talk_page_id):
    return title_to_id(id_to_title(int(talk_page_id)).replace("Talk:",""))

def classify_quality(encoder, directory, documents=None):

    t_f = open("text.tsv","r")

    y = []
    x = []
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

    print('Parsing quality... ')
    with open('quality.tsv','r') as f:
        i=0
        num_classified = 0
        for line in f:
            i+=1
            sys.stdout.write("\rLine: %d, Classified: %d, Classified & in model: %d   " % (i,num_classified,len(x)))
            sys.stdout.flush()
            try:
                article_id, article_quality = line.decode('utf-8', errors='replace').strip().split('\t')

                qual_mapping = classes[article_quality]
                num_classified+=1

                real_article_id = talk_to_real_id(article_id)
                doc_vector = encoder.model.docvecs[int(real_article_id)] 

                x.append(doc_vector)
                y.append(qual_mapping)

                counts[article_quality]+=1
            except:
                counts["unknown"]+=1

    sys.stdout.write("\n")

    sys.stdout.write(str(len(y))+" entries\n")
    for key,value in counts.iteritems():
        print("\t"+key+" - "+str(value)+" entries")
    print("\rFound %d classified articles" % len(y))
    print("Found %d classified articles with docvecs" % len(x))

    X = np.array(x)
    y = np.array(y)
    
    print('Training classifier...')
    for i in [100,500,1000,5000,10000,50000,100000,500000,1000000]:
        classifier = vector_classifier()
        t = time.time()
        classifier.train(X[:i+1], y[:i+1])
        print('Elapsed for %d: %0.2f' % (i,time.time()-t))
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

def get_article_quality(art_id,qualities):
    for l in qualities:
        if l.split("\t")[0]==art_id: return l.split("\t")[1]
    return None

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
            n_examples      = 5000000 # number of articles to consume per epoch 
            features        = 400   # vector length
            context_window  = 8     # words to analyze on either side of current word 
            threads         = 8     # number of worker threads during training
            epochs          = 100   # maximum number of epochs
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


        train_classifier = False 
        if train_classifier:

            #modl_d = "WikiLearn/data/models/old/5"
            modl_d = "WikiLearn/data/models/doc2vec"
            clas_d = "WikiLearn/data/models/classifier/"
            dict_d = "WikiLearn/data/models/doc2vec/text"

            #documents = text_corpus('text.tsv',n_examples=200000)
            #documents.get_phraser(dict_d)

            encoder = doc2vec()
            encoder.load(modl_d)

            print("length: %d" % len(encoder.model.docvecs))
            classify_quality(encoder,clas_d)

        map_talk_to_real = True 
        if map_talk_to_real:

            import Cython
            import subprocess 
            subprocess.Popen('python setup.py build_ext --inplace',shell=True).wait()
            from helpers import map_talk_to_real_ids
            map_talk_to_real_ids("id_mapping2.tsv") 

    else:
        print("text.tsv not present, could not create text dictionary")

    print("\nTotal time: %0.2f seconds" % (time.time()-start_time))

if __name__ == "__main__":
    main()


