#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os, sys, time, random
from shutil import rmtree

# enforce auto-flushing of stdout on every write
sys.stdout = os.fdopen(sys.stdout.fileno(),'w',0) 

import numpy as np

#                            Local imports
#-----------------------------------------------------------------------------#
from WikiParse.main           import download_wikidump, parse_wikidump, text_corpus
from WikiLearn.code.vectorize import doc2vec, make_seconds_pretty
from WikiLearn.code.classify  import vector_classifier_keras

from pathfinder import get_queries, astar_path

#                            Main function
#-----------------------------------------------------------------------------#

def classify_quality(encoder=None, directory=None, sequence=False):

    func_str = "Classifying quality"
    if sequence: func_str+=" by word-vector sequences (sentences)..."
    else: func_str+=" by doc-vectors"
    print("\n%s" % func_str)
    
    y = []
    x = []
    ids = []

    classes = {"fa":np.array([0],dtype=int),\
               "a":np.array([0],dtype=int),\
               "ga":np.array([0],dtype=int),\
               "bplus":np.array([0],dtype=int),\
               "b":np.array([0],dtype=int),\
               "c":np.array([1],dtype=int),\
               "start":np.array([2],dtype=int),\
               "stub" :np.array([2],dtype=int)}

    class_names = ["good","mid","poor"]

    counts  = {"good"   :0,\
               "mid"    :0,\
               "poor" :0,\
               "unknown/not_in_model":0}

    class_dict = {  "0": "good",\
                    "1": "mid",\
                    "2": "poor"}

    class_pretty = { "good": "\'good\'",\
                     "mid": "\'mid\' ",\
                     "poor": "\'poor\'"}

    class_str = ""
    for c in class_names:
        class_str+=c
        if class_names.index(c)!=len(class_names)-1: class_str+=" | "
    sys.stdout.write("Classes:\t\t%s\n"% (class_str))

    if sequence:

        ####
        max_quality_dict_size    = 100000 # if -1, no limit, o.w. total articles limited to this
        min_sentence_length_char = 60 # trim any sentences with less than this many characters
        sentence_length_words    = 8 # exact number of words per sentence
        print_sentences          = 0 # approx number of sentences to print during sentence encoding
        sentences_per_category   = 2000 # exact number of sentences to load in as training set

        drop_sentence_on_dropped_word = True # drop the whole sentence if one of its words isnt in model,
                                             # if false: drop just the word
        
        remove_stop_words = True # if True, removes stop words before calculating sentence lengths

        epochs = None        # if None, defaults to whats set in classify.py
        batch_size = None    # if None, defaults to whats set in classify.py

        # concatenate all words in doc to single sequence of maximum length 'document_max_num_words'
        treat_each_doc_as_single_sentence = True 
        if treat_each_doc_as_single_sentence:
            document_max_num_words        = 800
            drop_sentence_on_dropped_word = False
            docs_per_category             = 1000
            batch_size                    = 10
            document_min_num_words        = 500
        ####

        sys.stdout.write("Words/Sentence:    \t%d\n"%sentence_length_words)
        sys.stdout.write("Min. Char/Sentence:\t%d\n"%min_sentence_length_char)
        sys.stdout.write("Sentences/Class:   \t%d\n\n"%sentences_per_category)
        sys.stdout.write("Batch Size: %s\n"%("<default>" if batch_size is None else str(batch_size)))
        sys.stdout.write("Epochs:     %s\n\n"%("<default>" if epochs is None else str(epochs)))

        if remove_stop_words:
            stop_words_dict = {}
            stop_words = open("WikiLearn/data/stopwords/stopwords.txt").read().replace("\'","").split("\n")
            for s in stop_words:
                if s not in [""," "] and len(s)>0:
                    stop_words_dict[s] = True

        num_lines = len(open("quality.tsv","r").read().split("\n"))
        qf = open("quality.tsv","r")
        i=0
        qualities = {}
        for line in qf:
            i+=1
            if max_quality_dict_size!=-1 and i>max_quality_dict_size: break
            sys.stdout.write("\rCreating quality dict (%d/%d)"%(i,num_lines))
            try:
                article_id, article_quality = line.decode('utf-8', errors='replace').strip().split('\t')
                qualities[article_id] = article_quality
            except:
                i+=-1
                continue

        sys.stdout.write("\nEncoding english sentences to vector sequences...\n")
        qf.close()

        done_loading = False
        num_categories = len(class_names)

        approx_planned_sentences = num_categories*sentences_per_category 
        if treat_each_doc_as_single_sentence:
            approx_planned_sentences = num_categories*docs_per_category

        f = open("text.tsv","r")
        i=0
        enc_start_time = time.time()
        num_loaded=0
        for line in f:
            i+=1
            percent_done = "%0.1f%%" % (100.0*float(num_loaded)/float(approx_planned_sentences))
            perc_loaded = "%0.1f%%" % (100.0 *float(i)/13119700.0)
            sys.stdout.write("\rEncoding: %s done (%d/%d) | %s total | %s  "% (percent_done,num_loaded,approx_planned_sentences,perc_loaded,make_seconds_pretty(time.time()-enc_start_time)))
            sys.stdout.flush()
            try:
                article_id, article_contents = line.decode('utf-8', errors='replace').strip().split('\t')
            except: continue
                
            try: qual = classes[qualities[article_id]]
            except: 
                counts['unknown/not_in_model'] +=1
                continue

            qual_map = class_dict[str(qual[0])]

            if not treat_each_doc_as_single_sentence and counts[qual_map]>=sentences_per_category:  continue
            if treat_each_doc_as_single_sentence and counts[qual_map]>=docs_per_category: continue

            article_sentences = article_contents.split(". ")
            if treat_each_doc_as_single_sentence:
                full_doc = []
                full_doc_str = []
                doc_arr = np.zeros(shape=(document_max_num_words,300)).astype(float)

            for a in article_sentences:
                if len(a)<min_sentence_length_char and not treat_each_doc_as_single_sentence: 
                    continue 

                if treat_each_doc_as_single_sentence and len(full_doc)>=document_max_num_words: continue

                cleaned_a = a.replace(","," ").replace("(","").replace(")","")
                cleaned_a = cleaned_a.replace("&nbsp;","").replace("   "," ")
                cleaned_a = cleaned_a.replace("  "," ").lower()
                sentence_words = cleaned_a.split(" ")

                if remove_stop_words:
                    s_idx=0
                    while True:
                        try:
                            stop_words_dict[sentence_words[s_idx]]
                            del sentence_words[s_idx]
                        except:
                            s_idx+=1
                            if s_idx>=len(sentence_words): break

                word_vecs = []
                cur_sentence_length = 0
                if len(sentence_words)>=sentence_length_words:
                    for w in sentence_words:
                        try: 
                            word_vec = encoder.model[w.lower()]
                            if not treat_each_doc_as_single_sentence: word_vecs.append(word_vec)
                            else: 
                                full_doc.append(word_vec)
                                full_doc_str.append(w)
                            cur_sentence_length+=len(w)
                            
                        except: 
                            if drop_sentence_on_dropped_word:
                                cur_sentence_length=0
                                break
                            else: continue

                if treat_each_doc_as_single_sentence: continue # add full doc after for loop
                if cur_sentence_length<min_sentence_length_char: continue
                if len(word_vecs)==sentence_length_words: 
                    if random.randint(0,approx_planned_sentences)<print_sentences:
                        sys.stdout.write("\rExample %s sentence (decoded): %s\n"%(class_pretty[qual_map],cleaned_a))
                    x.append(word_vecs[:sentence_length_words])
                    y.append(qual)
                    counts[qual_map]+=1
                    num_loaded+=1
                    if min(counts["good"],counts["mid"],counts["poor"])>=sentences_per_category: 
                        done_loading = True
                        break
                    if counts[qual_map]==sentences_per_category: break
            
            if done_loading: break
            
            if treat_each_doc_as_single_sentence:
                if len(full_doc)<document_min_num_words: continue 
                if random.randint(0,approx_planned_sentences)<print_sentences:
                    sys.stdout.write("\rExample %s sentence (decoded): %s\n"%(class_pretty[qual_map],''.join(e+" " for e in full_doc_str)))

                for q in range(len(full_doc)):
                    if q==document_max_num_words: break
                    doc_arr[q,:] = full_doc[q]
                x.append(doc_arr)
                y.append(qual)
                counts[qual_map]+=1
                num_loaded+=1 
                if min(counts["good"],counts["mid"],counts["poor"])>=docs_per_category: 
                    break

        sys.stdout.write("\nTotal encoding time: %s" % make_seconds_pretty(time.time()-enc_start_time))
        del qualities

    else:
        num_lines = len(open("quality.tsv","r").read().split("\n"))
        sys.stdout.write('Parsing quality ')
        with open('quality.tsv','r') as f:
            i=0
            num_classified = 0
            for line in f:
                i+=1
                sys.stdout.write("\rParsing Quality: (%d|%d|%d), (model|class.|tot.)" % (len(x),num_classified,num_lines))
                try:
                    article_id, article_quality = line.decode('utf-8', errors='replace').strip().split('\t')

                    qual = classes[article_quality]
                    num_classified+=1

                    doc_vector = encoder.model.docvecs[int(article_id)] 
                    x.append(doc_vector)
                    y.append(qual)

                    if qual==0: counts["good"] +=1
                    if qual==1: counts["mid"]  +=1
                    if qual==2: counts["poor"] +=1
                except:
                    counts["unknown/not_in_model"]+=1

    sys.stdout.write("\n")
    
    '''
    for key,value in counts.iteritems():
        print("\t"+key+" - "+str(value)+" entries")
    '''

    classifier = vector_classifier_keras(class_names=class_names,directory=directory)
    y = np.ravel(np.array(y))

    if sequence:
        X = np.array(x)
        print(X.shape)
        t = time.time()
        classifier.train_seq(X,y,epochs=epochs,batch_size=batch_size)        
    else:
        X = np.array(x)
        t = time.time()
        classifier.train(X,y)    

    print('Elapsed for %d: %0.2f' % (i,time.time()-t))

    '''
    print("\nEnter sentences to test model (q to quit)...")
    while True:
        sentence = raw_input("> ")
        if sentence=="q": return
        docvec = np.ravel(self.encoder.model.infer_vector(sentence.split()))
        print(model.predict(docvec,batch_size=1,verbose=1))
    '''
        
# returns the most recent trained model (according to naming scheme)
def get_most_recent_model(directory):
    model_dirs = os.listdir(directory)
    most_recent_model_dir = ""
    most_recent_model_time = 0 
    for m in model_dirs:
        try:
            cur_time = int(m.split("-")[0].split(":")[1])
            if cur_time>most_recent_model_time:
                most_recent_model_dir = m 
                most_recent_model_time = cur_time 
        except: continue
    return os.path.join(directory,most_recent_model_dir)

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
        train_quality_classifier = True 
        if train_quality_classifier:
            
            #model_dir = get_most_recent_model('WikiLearn/data/models/doc2vec')
            #model_dir = get_most_recent_model('/home/bfaure/Desktop/WikiClassify2.0/WikiLearn/data/models/doc2vec')
            model_dir = "/media/bfaure/Local Disk/Ubuntu_Storage" # holding full model on ssd for faster load

            # very small model for testing
            model_dir = "/home/bfaure/Desktop/WikiClassify2.0 extra/WikiClassify Backup/(2)/doc2vec/older/5"


            classifier_dir = "WikiLearn/data/models/classifier/recent" # directory to save classifier to
            encoder = doc2vec()
            encoder.load(model_dir)

            #classify_quality(encoder,classifier_dir)
            classify_quality(encoder=encoder,directory=classifier_dir,sequence=True)

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

    print("\nTotal time: %s seconds" % make_seconds_pretty(time.time()-start_time))

if __name__ == "__main__":
    main()


