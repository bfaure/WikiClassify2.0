#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os, sys, time
from shutil import rmtree

# enforce auto-flushing of stdout on every write
sys.stdout = os.fdopen(sys.stdout.fileno(),'w',0) 

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
            #sys.stdout.flush()
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
    
    print('Training classifier...')
    for i in [100,500,1000,5000,10000,50000,100000,500000,1000000]:
        classifier = vector_classifier()
        t = time.time()
        classifier.train(X[:i+1], y[:i+1])
        print('Elapsed for %d: %0.2f' % (i,time.time()-t))
        classifier.save(directory)
    
    #classifier = vector_classifier()
    #classifier.train(X,y)
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
    start_time = time.time()

    # command line argument to open the gui window
    if len(sys.argv)==2 and sys.argv[1] in ["-g","-gui"]:
        from interface import start_gui
        start_gui()
        return

    require_datadump = False
    if require_datadump:
        if not os.path.isfile('text.tsv'):
            # download (if not already present)
            dump_path = download_wikidump('enwiki','WikiParse/data/corpora/enwiki/data')
            # parse the .xml file
            parse_wikidump(dump_path)

    # if we have a copy of the parsed datadump
    if os.path.isfile('text.tsv'):


        # after parser is run, use this to map the article ids (talk ids) in quality.tsv 
        # to the article ids (real article ids) in text.tsv, saved in id_mapping.tsv
        map_talk_to_real = False 
        if map_talk_to_real:
            import Cython
            import subprocess 
            subprocess.Popen('python setup.py build_ext --inplace',shell=True).wait()
            from helpers import map_talk_to_real_ids
            map_talk_to_real_ids("id_mapping.tsv")         


        # trains a new Doc2Vec encoder on the contents of text.tsv
        run_doc2vec = False
        if run_doc2vec:

            # training configuration
            n_examples      = 20000000 # number of articles to consume per epoch 
            features        = 300      # vector length
            context_window  = 8        # words to analyze on either side of current word 
            threads         = 8        # number of worker threads during training
            epochs          = 20       # maximum number of epochs
            pass_per_epoch  = 1        # number of passes across corpus / epoch (gensim default:5)
            print_epoch_acc = True     # print the accuracy after each epoch
            stop_early      = True     # cut off training if accuracy falls 
            backup          = True     # if true, model is saved after each epoch with "-backup" in filename

            model_name  = "unix:%d-examples:%d-features:%d-window:%d-epochs:%d-ppe:%d" % (int(time.time()),n_examples,features,context_window,epochs,pass_per_epoch)
            phraser_dir = 'WikiLearn/data/models/dictionary/text'         # where to save/load phraser from
            model_dir   = "WikiLearn/data/models/doc2vec/%s" % model_name # where to save new doc2vec model

            # print out launch config
            print("\nphraser_dir: %s" % phraser_dir)
            print("model_dir:   %s\n" % (' | '.join(x for x in model_name.split("-"))))

            # create corpus object to allow for text tagging/iteration
            documents = text_corpus('text.tsv', n_examples=n_examples)
            # assemble bigram/trigrams from corpus
            documents.get_phraser(phraser_dir)
            # create doc2vec object    
            encoder = doc2vec()
            # set model hyperparameters
            encoder.build(features=features,context_window=context_window,threads=threads,iterations=pass_per_epoch)
            # train model on text corpus
            encoder.train(corpus=documents,epochs=epochs,directory=model_dir,test=print_epoch_acc,stop_early=stop_early,backup=backup)


        # after Doc2Vec has created vector encodings, this trains on those
        # mappings using the quality.tsv data as the output
        train_quality_classifier = False 
        if train_quality_classifier:
            print("WORK IN PROGRESS!!!")
            return
            encoder_dir = 'Wikilearn/data/models/doc2vec/xxxx'
            modl_d = "WikiLearn/data/models/old/5"
            clas_d = "WikiLearn/data/models/classifier/recent"
            encoder = doc2vec()
            encoder.load(modl_d)
            classify_quality(encoder,clas_d)


        # after the data has been pushed to the server, we need to run a 2nd pass
        # to add all of the quality and importance attributes
        push_quality_importance = False 
        if push_quality_importance:
            
            if not os.path.isfile("id_mapping.tsv"):
                print("File id_mapping.tsv must be present to perform this task")
                return

            if not os.path.isfile("quality.tsv"):
                print("File quality.tsv must be present to perform this task")
                return

            if not os.path.isfile("importance.tsv"):
                print("File importance.tsv must be present to perform this task")
                return

            import psycopg2
            from psycopg2 import connect
            from bisect import bisect_left

            # connecting to database
            username = "waynesun95"
            host = "aa9qiuq51j8l7b.cja4xyhmyefl.us-east-1.rds.amazonaws.com"
            port = "5432"
            dbname = "ebdb"
            password = raw_input("Enter server password: ")

            sys.stdout.write("Trying to connect... ")
            try:
                server_conn = connect("user="+username+" host="+host+" port="+port+" password="+password+" dbname="+dbname)
            except:
                sys.stdout.write("failure\n")
                return
            sys.stdout.write("success\n")

            # getting all ids in the database
            cursor = server_conn.cursor()
            command = "SELECT id FROM articles"

            sys.stdout.write("Requesting all article ids... ")
            try:
                cursor.execute(command)
                data = cursor.fetchall()
            except:
                sys.stdout.write("failure\n")
                return
            sys.stdout.write("success\n")
            cursor.close()

            if data is not None:
                num_rows = len(data)
                if num_rows==0:
                    print("Table is empty!")
                    return
                print("Found %d rows in table" % num_rows)
            else:
                print("Data received is None!")
                return 

            # returns the real id for a given .tsv file row
            def get_real_id(row):
                return int(row.split("\t")[1])

            # opening the id_mapping.tsv file 
            print("Reading id_mapping.tsv...")
            id_mapping = open("id_mapping.tsv","r").read().split("\n")
            rows = []
            for row in id_mapping:
                items = row.split("\t")
                if len(items)==2: rows.append(row)
            print("Sorting id mappings by real id...")
            rows = sorted(rows,key=get_real_id)
            print("Splitting id mappings...")
            ids_talk = []
            ids_real = []
            for r in rows:
                items = r.split("\t")
                ids_talk.append(int(items[0]))
                ids_real.append(int(items[1]))

            # returns index of input query in ids_real list
            def binary_search(query,lo=0,hi=None):
                hi = hi or len(ids_real)
                return bisect_left(ids_real,query,lo,hi)

            # returns the talk page id for a given real page id
            def real_to_talk_id(real_page_id):
                return ids_talk[binary_search(real_page_id)]

            # opening the quality.tsv file
            print("Reading quality.tsv...")
            qual_mapping = open("quality.tsv","r").read().split("\n")
            q_rows = []
            for row in qual_mapping:
                items = row.split("\t")
                if len(items)==2: q_rows.append(row)

            # opening the importance.tsv file 
            print("Reading importance.tsv...")
            imp_mapping = open("importance.tsv","r").read().split("\n")
            i_rows = []
            for row in imp_mapping:
                items = row.split("\t")
                if len(items)==2: i_rows.append(row)

            print("Creating quality,importance dictionary...")
            qual_imp_dict = {}
            for c_q,c_i in zip(q_rows,i_rows):
                cur_id,quality = c_q.split("\t")
                o_id,importance = c_i.split("\t")
                if cur_id!=o_id:
                    print("ERROR: cur_id!=o_id")
                    return
                qual_imp_dict[str(cur_id)] = [quality,importance] 

            # returns the quality for a given real_article_id
            def get_quality_importance(real_article_id):
                talk_id = str(real_to_talk_id(real_article_id))
                return qual_imp_dict[talk_id]

            # iterate over all real ids in the server 
            sys.stdout.write("Processing...")
            seen_ids = []
            resp_qual = []
            resp_imp = []
            i=0
            dropped=0
            for r in data:
                i+=1
                sys.stdout.write("\rProcessing (%d/%d)   " % (i,num_rows))
                cur_id = r[0]
                try:
                    qual,imp = get_quality_importance(cur_id)
                    seen_ids.append(str(cur_id))
                    resp_qual.append(str(qual))
                    resp_imp.append(str(imp))
                except: dropped+=1
            sys.stdout.write("\n")
            if dropped>0: print("Dropped %d articles due to error" % dropped)

            # TODO: make the update buffered

            # sending all of the qualities and importances to the server
            sys.stdout.write("Sending to server...")
            for i in range(len(seen_ids)):
                cursor = server_conn.cursor()
                command = "UPDATE articles SET quality = \'"+resp_qual[i]+"\', importance = \'"+resp_imp[i]+"\' "
                command += "WHERE id = "+seen_ids[i]+";"
                cursor.execute(command)
                sys.stdout.write("\rSending to server (%d/%d)   " % (i,len(seen_ids)))
                cursor.close()
            server_conn.commit()
            sys.stdout.write("\n")
            print("Done")

    else:
        print("text.tsv not present, could not create text dictionary")

    print("\nTotal time: %0.2f seconds" % (time.time()-start_time))

if __name__ == "__main__":
    main()


