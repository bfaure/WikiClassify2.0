#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os, requests, sys, random, re, tarfile, codecs, bz2, time
random.seed(0)
reload(sys);
sys.setdefaultencoding("utf-8")

from urlparse import urlparse
from subprocess import call
from lxml import html
from urllib import urlretrieve
from urlparse import urlparse

#                             Third-party imports
#-----------------------------------------------------------------------------#
import numpy as np

from gensim import utils
from gensim.models.doc2vec     import TaggedDocument
from gensim.models.phrases     import Phraser, Phrases
from gensim.corpora.dictionary import Dictionary
from gensim.corpora.mmcorpus   import MmCorpus

from sklearn.preprocessing import MultiLabelBinarizer


#                             Global functions
#-----------------------------------------------------------------------------#

def download_wikidump(corpus_name, directory):
    url  = 'https://dumps.wikimedia.org/{0}/latest/{0}-latest-pages-meta-current.xml.bz2'.format(corpus_name)
    file_path = download(url, directory)
    file_path = expand_bz2(file_path)
    return file_path

def download(url, directory):
    if not os.path.isdir(directory): os.makedirs(directory)
    file_name = os.path.basename(urlparse(url)[2])
    file_path = os.path.join(directory, file_name)
    sys.stdout.write("\tDownloading '%s'... " % file_name)
    if not os.path.isfile(file_path):
        try:
            with open(file_path, "wb") as f:
                response = requests.get(url, stream=True)
                total_length = response.headers.get('content-length')
                megabytes = int(total_length)/1000000
                sys.stdout.write(str(megabytes)+" MB\n")
                start_time = time.time()

                if total_length is not None:
                    dl = 0
                    total_length = int(total_length)
                    for data in response.iter_content(chunk_size=4096):
                        dl += len(data)
                        f.write(data)
                        num_items = int( float(dl)/float(total_length)*float(25) )
                        progress_string = ""
                        for prog_index in range(25):
                            if prog_index<=num_items: progress_string+="-"
                            else: progress_string += " "

                        rem_secs = (total_length-dl)/(dl/(time.time()-start_time)) # total seconds remaining
                        rem_hours = int(rem_secs/3600)                 
                        rem_mins = int((rem_secs-(rem_hours*3600))/60) 
                        rem_secs = int(rem_secs-(rem_hours*3600)-(rem_mins*60)) 
                        rem_time_str = "ETA: "+str(rem_hours)+"h "+str(rem_mins)+"m "+str(rem_secs)+"s"

                        sys.stdout.write("\r\t\t["+progress_string+"] "+str(100.0*dl/total_length)[:4]+"% done | "+rem_time_str+"  ")
                        sys.stdout.flush()
                    sys.stdout.write("\n")
                else:
                    f.write(response.content)
        except:
            print("\t\tCould not download '%s'." % file_name)
    else:
        print("\t\t'%s' already exists." % file_name)
    return file_path

def expand_bz2(file_path):
    sys.stdout.write("\tExpanding bz2... ")
    if not os.path.isfile(file_path[:-4]):
        file_size = os.path.getsize(file_path)
        estimated_file_size = (float(5)*float(file_size))/1000.0
        sys.stdout.write("Estimated "+str(estimated_file_size)+" MB\n")
        try:
            with open(file_path[:-4], 'wb') as new_file, bz2.BZ2File(file_path, 'rb') as file:
                for data in iter(lambda : file.read(100 * 1024), b''):
                    new_file.write(data)

                    num_items = int( float(file.tell())/float(file_size)*float(5) )
                    progress_string = ""
                    for prog_index in range(25):
                        if prog_index <= num_items: progress_string+="-"
                        else: progress_string += " "
                    sys.stdout.write("\r\t\t["+progress_string+"] "+str(100.0*file.tell()/file_size)[:5]+"% done")
                    sys.stdout.flush()
                sys.stdout.write("\n")
        except:
            print("\t\tCould not expand file.")
    else:
        print("\t\tFile already expanded.")
    return file_path[:-4]

def parse_wikidump(dump_path, cutoff_date='20010115', creds=None):
    #if password==None: password = raw_input("Database password: ")

    if creds is not None:
        # retrieve passed server credentials
        password = creds.server_password
        host     = creds.server_host
        username = creds.server_username
        port     = creds.server_port
        dbname   = creds.server_dbname
    else:
        # set to defaults to tell C++ not to use server
        password    = "NONE"
        host        = "NONE"
        username    = "NONE"
        port        = "NONE"
        dbname      = "NONE"

    compiled = True
    if compiled:
        try:
            print("\tCompiling parser...")
            scripts = ["WikiParse/code/"+x for x in ["main.cpp","wikidump.cpp","wikipage.cpp","wikitext.cpp","string_utils.cpp"]]
            call(["g++","--std=c++11","-O3"]+scripts+["-lpqxx","-lpq","-o","wikiparse.out"])
        except:
            return False

    if os.path.isfile('wikiparse.out'):
        if os.name == "nt":
            print("\tDetected Windows, altering command...")
            print("\tCalling wikiparse.out...")
            call(["wikiparse.out",dump_path,cutoff_date,password,host,username,port,dbname])
            return True
        else:
            print("\tCalling ./wikiparse.out...")
            call(["./wikiparse.out", dump_path, cutoff_date,password,host,username,port,dbname])
            return True
    else:
        print("\tERROR: Could not find wikiparse.out")
        return False

def gensim_corpus(tsv_path, directory, make_phrases=False):
    text = text_corpus(tsv_path)
    text.get_dictionary(directory)
    if make_phrases:
            text.get_phraser(directory)
    return text

#                      Tagged Document iterator
#-----------------------------------------------------------------------------#

def tokenize(text):
    return re.split('\W+', utils.to_unicode(text).lower())

class text_corpus(object):

    def __init__(self, tsv_path, n_examples=100000):
        self.n_examples = n_examples
        self.document_path = tsv_path
        self.document_size = os.path.getsize(tsv_path)
        self.instances = sum(1 for line in open(tsv_path))
        self.bigram = Phraser(Phrases())
        self.trigram = Phraser(Phrases())

    def __iter__(self):
        for i, doc in self.indexed_docs():
            yield TaggedDocument(self.process(doc),[i])

    def process(self, text):
        return self.trigram[self.bigram[tokenize(text)]]

    def bags(self, read_all=False):
        return bag_corpus(self, read_all)

    def docs(self, read_all=False):
        for _, doc in self.indexed_docs(read_all=read_all):
            yield self.process(doc)

    def indexed_docs(self, read_all=False):
        current_example = 0
        with open(self.document_path,'rb') as fin:
            for line in fin:
                if (current_example < self.n_examples) or read_all:
                    if line.strip().count('\t') == 1 and line.count(' ') > 1:
                        i, doc = line.decode('utf-8', errors='replace').strip().split('\t')
                        yield i,doc
                else:
                    raise StopIteration
                current_example += 1

    def get_phraser(self, directory, sensitivity=2):

        if not os.path.isdir(directory):
            os.makedirs(directory)

        print("\t\tGetting bigram detector...")
        if not os.path.isfile(directory+'/bigrams.pkl'):
            self.bigram = Phraser(Phrases(self.docs(read_all=True), min_count=2, threshold=sensitivity, max_vocab_size=2000000))
            self.bigram.save(directory+'/bigrams.pkl')
        else:
            self.bigram  = Dictionary.load(directory+'/bigrams.pkl')

        print("\t\tGetting trigram detector...")
        if not os.path.isfile(directory+'/trigrams.pkl'):
            self.trigram = Phraser(Phrases(self.bigram[self.docs(read_all=True)], min_count=2, threshold=sensitivity, max_vocab_size=2000000))
            self.trigram.save(directory+'/trigrams.pkl')
        else:
            self.trigram = Dictionary.load(directory+'/trigrams.pkl')

    def load_phraser(self, directory):
        print("\tLoading gram detector...")
        self.bigram  = Dictionary.load(directory+'/bigrams.pkl')
        self.trigram = Dictionary.load(directory+'/trigrams.pkl')

    def get_dictionary(self, directory):
        if not os.path.isdir(directory):
            os.makedirs(directory)
        if not os.path.isfile(directory+'/dictionary.dict'):
            print("\tBuilding dictionary...")
            self.dictionary = Dictionary(self.docs(read_all=True), prune_at=2000000)
            print("\tFiltering dictionary extremes...")
            self.dictionary.filter_extremes(no_below=5, no_above=0.5, keep_n=2000000)
            print("\tSaving dictionary...")
            self.dictionary.save(directory+'/dictionary.dict')
            self.dictionary.save_as_text(directory+'/word_list.tsv')
        else:
            self.load_dictionary(directory)

    def load_dictionary(self, directory):
        print("\tLoading dictionary...")
        self.dictionary = Dictionary.load(directory+'/dictionary.dict')

class bag_corpus(object):

    def __init__(self, text_corpus, read_all):
        self.text_corpus = text_corpus
        self.read_all    = read_all

    def __iter__(self):
        for doc in self.text_corpus.docs(self.read_all):
            yield self.text_corpus.dictionary.doc2bow(doc)
