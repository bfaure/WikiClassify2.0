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

import imageio
from keras.layers import Embedding 
#                            Local imports
#-----------------------------------------------------------------------------#
from WikiParse.main           import download_wikidump, parse_wikidump, text_corpus
from WikiLearn.code.vectorize import doc2vec, make_seconds_pretty
from WikiLearn.code.classify  import vector_classifier_keras

from pathfinder import get_queries, astar_path

#                            Main function
#-----------------------------------------------------------------------------#

qualities = None # used by get_quality_documents, cross-call variable
stop_words_dict = None # used by get_quality_documents, cross-call variable
most_common_dict = None #
class_dict = None 
class_pretty = None 
classes = None 
# Returns the first sequences_per_class good, mid, and poor article bodies, converted to word vectors
# single sequence of word vectors returned for each article, if a start_at value is specified, will 
# traverse into the text.tsv file that far (line-wise) before starting to add documents to the data
def get_quality_documents(  
    encoder,
    seq_per_class,
    min_words_per_seq,
    max_words_per_seq,
    start_at=0,
    print_avg_length=False,
    remove_stop_words=True,
    trim_vocab_to=-1,
    replace_non_model=False,
    swap_with_word_idx=False,
    class_names=["good","mid","poor"],
    class_map={"fa":0,"a":0,"ga":0,"bplus":0,"b":0,"c":1,"start":2,"stub":2}
    ):
    
    global qualities 
    global stop_words_dict 
    global most_common_dict
    global class_dict
    global class_pretty
    global classes

    y   = []
    x   = []

    if classes==None:
        classes = {"fa":np.array([class_map["fa"]],dtype=int),\
                    "a":np.array([class_map["a"]],dtype=int),\
                    "ga":np.array([class_map["ga"]],dtype=int),\
                    "bplus":np.array([class_map["bplus"]],dtype=int),\
                    "b":np.array([class_map["b"]],dtype=int),\
                    "c":np.array([class_map["c"]],dtype=int),\
                    "start":np.array([class_map["start"]],dtype=int),
                    "stub":np.array([class_map["stub"]],dtype=int)}

    longest_class_len = 0
    counts = {}
    for n in class_names:
        if len(n)>longest_class_len:
            longest_class_len = len(n)
        counts[n] = 0
    counts["unknown/not_in_model"]=0

    if class_dict==None:
        class_dict = {}
        for i in range(len(class_names)):
            class_dict[str(i)] = class_names[i]

    if class_pretty==None:
        class_pretty = {}
        for i in range(len(class_names)):
            class_name_pretty = class_names[i]
            while len(class_name_pretty)<=longest_class_len:
                class_name_pretty+=" "
            class_pretty[class_names[i]]=class_name_pretty

    class_lengths = {}
    for c in class_names:
        class_lengths[c]=0

    zero_vector = [0.00]*300 

    max_quality_dict_size    = -1 # if -1, no limit, o.w. total articles limited to this
    print_sentences          = 0 # approx number of sentences to print during sentence encoding

    # create stop words dictionary if not yet loaded
    if remove_stop_words and stop_words_dict==None:
        stop_words_dict = {}
        #stop_words = open("WikiLearn/data/stopwords/stopwords.txt").read().replace("\'","").split("\n")
        stop_words = open("WikiLearn/data/stopwords/stopwords_long.txt","r").read().replace("\'","").split("\n")
        for s in stop_words:
            if s not in [""," "] and len(s)>0:
                stop_words_dict[s] = True

    # create dictionary containing top 'trim_vocab_to' highest frequency words
    if ((trim_vocab_to!=-1 or swap_with_word_idx) and most_common_dict==None):
        most_common_dict = {}
        word_list = open("WikiLearn/data/models/dictionary/text/word_list.tsv","r").read().split("\n")
        w_idx=0
        for w in word_list:
            items = w.split("\t")
            #if len(items)==3 and int(items[2])>trim_vocab_to:
            if len(items)==3 and int(items[2])>3000:
                try:
                    in_model = encoder.model[items[1].lower()]
                    most_common_dict[items[1]]=w_idx 
                    w_idx+=1
                except:
                    continue
        print("Word List Size: %d"%len(most_common_dict.keys()))

    # Create the qualities dictionary if not yet loaded
    if qualities==None:
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
        sys.stdout.write("\n")
        qf.close()
    # number of total items we will have to load (sentences or docs)
    approx_total = len(class_names)*seq_per_class
    f = open("text.tsv","r")
    i=0
    enc_start_time = time.time()
    num_loaded=0
    eof=True 
    # iterate over each line (document) in text.tsv
    for line in f:
        i+=1
        # skip
        if i<start_at: continue
        percent_done = "%0.1f%%" % (100.0*float(num_loaded+1)/float(approx_total))
        perc_loaded  = "%0.1f%%" % (100.0 *float(i)/13119700.0)
        sys.stdout.write("\rEncoding: %s done (%d/%d) | %s total | %s  "% (percent_done,num_loaded+1,approx_total,perc_loaded,make_seconds_pretty(time.time()-enc_start_time)))
        sys.stdout.flush()
        
        # load in the current line
        try:    article_id, article_contents = line.decode('utf-8', errors='replace').strip().split('\t')
        except: continue
        # see if this article has a quality mapping
        try: qual = classes[qualities[article_id]]
        except: 
            # skip article if no listed quality
            counts['unknown/not_in_model'] +=1
            continue
        # get the number we are using as the y for this quality (0,1,2,etc)
        qual_map = class_dict[str(qual[0])]
        # if we have already loaded the maximum number of articles in this category
        if counts[qual_map]>=seq_per_class: continue
        # split article into sentences
        article_sentences = article_contents.split(". ")
        # create elems to hold entire document (if saving as single seq)
        full_doc = []
        full_doc_str = []
        doc_arr = np.zeros(shape=(max_words_per_seq,300)).astype(float)
        # iterate over each sentence in the article
        for a in article_sentences:
            if len(full_doc)>=max_words_per_seq: break
            # minor text cleaning
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

            #if len(sentence_words)>=sentence_length_words:
            for w in sentence_words:
                if trim_vocab_to!=-1 or swap_with_word_idx:
                    try: 
                        idx = most_common_dict[w.lower()]
                    except: 

                        continue
                try: 
                    word_vec = encoder.model[w.lower()]
                    if swap_with_word_idx:
                        full_doc.append(most_common_dict[w.lower()])
                    else:
                        full_doc.append(word_vec)
                    full_doc_str.append(w)
                except: 
                    if replace_non_model:
                        if swap_with_word_idx:
                            full_doc.append(0)
                        else:
                            full_doc.append(zero_vector)
                        full_doc_str.append(w)
                    continue
        # add the document
        if len(full_doc)<min_words_per_seq: continue 
        if random.randint(0,approx_total)<print_sentences:
            sys.stdout.write("\rExample %s sentence (decoded): %s\n"%(class_pretty[qual_map],''.join(e+" " for e in full_doc_str[:10])+"..."))
        for q in range(len(full_doc)):
            if q==max_words_per_seq: break
            doc_arr[q,:] = full_doc[q]
        x.append(doc_arr)
        y.append(qual)
        counts[qual_map]+=1
        class_lengths[qual_map]+=len(full_doc)
        num_loaded+=1 
        if min(counts["good"],counts["mid"],counts["poor"])>=seq_per_class: 
            eof=False
            break
    #sys.stdout.write("\nTotal encoding time: %s\n" % make_seconds_pretty(time.time()-enc_start_time))
    sys.stdout.write("\n")
    f.close()
    if print_avg_length:
        for key,value in class_lengths.iteritems():
            print("%s avg length (words): %0.1f"%(key,float(value/seq_per_class)))
        sys.stdout.write("\n")
    y = np.ravel(np.array(y))
    X = np.array(x)
    if eof: i=-1 # denote eof
    return X,y,i 

def make_gif(parent_folder):
    items = os.listdir(parent_folder)
    png_filenames = []
    for elem in items:
        if elem.find(".png")!=-1 and elem.find("heatmap")!=-1:
            png_filenames.append(elem)

    sorted_png = []
    while True:
        lowest = 10000000
        lowest_idx = -1
        for p in png_filenames:
            iter_val = int(p.split("-")[2].split(":")[1])
            epoch_val = int(p.split("-")[3].split(":")[1].split(".")[0])
            val = float(iter_val)+0.1*epoch_val

            if lowest_idx==-1 or val<lowest:
                lowest = val
                lowest_idx = png_filenames.index(p)

        sorted_png.append(png_filenames[lowest_idx])
        del png_filenames[lowest_idx]
        if len(png_filenames)==0: break
    png_filenames = sorted_png

    with imageio.get_writer(parent_folder+"/prediction-heatmap.gif", mode='I',duration=0.3) as writer:
        for filename in png_filenames:
            image = imageio.imread(parent_folder+"/"+filename)
            writer.append_data(image)

def classify_quality(encoder=None, directory=None, gif=True, model_type="cnn"):
    print("\nClassifying quality by word-vector sequences...\n")

    class_names = ["good","mid","poor"]
    class_str = ""
    for c in class_names:
        class_str+=c
        if class_names.index(c)!=len(class_names)-1: class_str+=" | "
    sys.stdout.write("Classes:\t\t%s\n"% (class_str))

    #### SETTINGS
    #dpipc = 213 # documents per iteration per class, limited by available memory
    #dpipc = 320
    #dpipc = 640
    #dpipc = 960
    dpipc = 1280
    #min_words = 90 # trim any documents with less than this many words
    min_words = 20
    #max_word=100
    max_words = 20 # maximum number of words to maintain in each document
    remove_stop_words = False # if True, removes stop words before calculating sentence lengths
    limit_vocab_size = 20000 # if !=-1, trim vocab to 'limit_vocab_size' words
    batch_size = None    # if None, defaults to whats set in classify.py, requires vram
    replace_non_model = True # replace words not found in model with zero vector
    swap_with_word_idx = False
    epochs=1
    ####

    # if using CNN, this must be non -1
    if model_type=="cnn":
        if limit_vocab_size==-1:
            print("WARNING: limit_vocab_size must be non -1 for CNN")
            sys.exit(0)
        remove_stop_words=True
        #replace_non_model=True
        swap_with_word_idx=False


    sys.stdout.write("Max Words/Doc:     \t%d\n"%max_words)
    sys.stdout.write("Min Words/Doc:     \t%d\n"%min_words)
    sys.stdout.write("Docs/Class:        \t%d\n\n"%dpipc)
    sys.stdout.write("Batch Size: %s\n"%("<default>" if batch_size is None else str(batch_size)))
    sys.stdout.write("Epochs:     %s\n\n"%("<default>" if epochs is None else str(epochs)))

    test_on_epochs = True

    classifier = vector_classifier_keras(class_names=class_names,directory=directory,model_type=model_type,vocab_size=limit_vocab_size)
    doc_idx = 0
    i=0
    while True:
        i+=1

        #if i>10: break

        print("\nIteration %d"%i)
        X,y,doc_idx = get_quality_documents(encoder, dpipc, min_words, max_words, doc_idx,\
                                             remove_stop_words=remove_stop_words,\
                                             trim_vocab_to=limit_vocab_size,\
                                             replace_non_model=replace_non_model,
                                             swap_with_word_idx=swap_with_word_idx)

        embedding_layer=None

        last_loss=None 
        num_worse=0
        for j in range(epochs):
            #plot = True if j==epochs-1 else False
            plot=True
            loss = classifier.train_seq_iter(X,y,i,j,plot=plot,embedding_layer=embedding_layer)
            if last_loss==None: last_loss=loss 
            else:
                if loss>last_loss:
                    num_worse+=1
                else:
                    num_worse=0
            if num_worse>1:
                break

        #if test_on_epochs:

        if doc_idx==-1: break

    # write out ordered gif of all items in picture directory (heatmaps)
    if gif: make_gif(classifier.pic_dir)

    sys.stdout.write("\nReached end of text.tsv")
    #test_model_interactive(classifier,encoder)


def test_model_interactive(classifier,encoder):
    print("\nEnter sentences to test model (q to quit)...")
    while True:
        sentence = raw_input("> ")
        if sentence=="q": return
        docvec = np.ravel(self.encoder.model.infer_vector(sentence.split()))
        print(model.predict(docvec,batch_size=1,verbose=1))

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

            # directory to save classifier to
            classifier_dir = "WikiLearn/data/models/classifier/keras" 

            encoder = doc2vec()
            encoder.load(model_dir)

            classify_quality(encoder,classifier_dir)
            #classify_quality(encoder=encoder,directory=classifier_dir,sequence=True)

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

    print("\nTotal time: %s\n" % make_seconds_pretty(time.time()-start_time))

if __name__ == "__main__":
    main()


