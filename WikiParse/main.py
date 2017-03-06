#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os, requests, sys, random, re, tarfile, codecs, bz2
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
    if not os.path.isdir(directory):
        os.makedirs(directory)
    file_name = os.path.basename(urlparse(url)[2])
    file_path = os.path.join(directory, file_name)
    print("\t\tDownloading '%s'..." % file_name)
    if not os.path.isfile(file_path):
        try:
            with open(file_path, "wb") as f:
                response = requests.get(url, stream=True)
                total_length = response.headers.get('content-length')
                if total_length is not None:
                    dl = 0
                    total_length = int(total_length)
                    for data in response.iter_content(chunk_size=4096):
                        dl += len(data)
                        f.write(data)
                        sys.stdout.write("\r\t\t\t%0.1f%% done" % (100.0*dl/total_length))    
                        sys.stdout.flush()
                    print('')
                else:
                    f.write(response.content)
        except:
            print("\t\t\tCould not download '%s'." % file_name)
    else:
        print("\t\t\t'%s' already exists." % file_name)
    return file_path

def expand_bz2(file_path):
    print("\t\tExpanding bz2...")
    if not os.path.isfile(file_path[:-4]):
        file_size = os.path.getsize(file_path)
        try:
            with open(file_path[:-4], 'wb') as new_file, bz2.BZ2File(file_path, 'rb') as file:
                for data in iter(lambda : file.read(100 * 1024), b''):
                    new_file.write(data)
                    sys.stdout.write("\r\t\t\t%0.1f%% done" % (100.0*file.tell()/file_size))    
                    sys.stdout.flush()
        except:
            print("\t\t\tCould not expand file.")
    else:
        print("\t\t\tFile already expanded.")
    return file_path[:-4]

def parse_wikidump(dump_path, cutoff_date='20010115'):
    dump_path = 'WikiParse/data/corpora/simplewiki/data/simplewiki-latest-pages-meta-current.xml'
    compiled = False
    if compiled:
        try:
            print("\tCompiling parser...")
            scripts = ["WikiParse/code/"+x for x in ["main.cpp","wikidump.cpp","wikipage.cpp","wikitext.cpp","string_utils.cpp"]]
            call(["g++","--std=c++11","-O3"]+scripts+["-o","wikiparse.out"])
        except:
            return False
    if os.path.isfile('wikiparse.out'):
        print("\tCalling ./wikiparse.out...")
        if os.name == "nt":
            print("\tDetected Windows, altering command...")
            call(["wikiparse.out",dump_path,cutoff_date])
        else:
            call(["./wikiparse.out", dump_path, cutoff_date])
    else:
        print("\tERROR: Could not find wikiparse.out")

def gensim_corpus(tsv_path, directory, make_phrases=False,):
    text = text_corpus(tsv_path)
    if not os.path.isfile(directory+'/dictionary.dict'):
        text.train_dictionary()
        text.save_dictionary(directory)
    else:
        text.load_dictionary(directory)
    if make_phrases:
        if not os.path.isfile(directory+'/bigrams.pkl'):
            text.train_phraser()
            text.save_phraser(directory)
        else:
            text.load_phraser(directory)
    return text

#                      Tagged Document iterator
#-----------------------------------------------------------------------------#

def tokenize(text):
    return re.split('\W+', utils.to_unicode(text).lower())

class text_corpus(object):

    def __init__(self, tsv_path):
        self.document_path = tsv_path
        self.instances = sum(1 for line in open(tsv_path))
        self.bigram = Phraser(Phrases())
        self.trigram = Phraser(Phrases())

    def __iter__(self):
        for i, doc in self.indexed_docs():
            yield TaggedDocument(self.process(doc),[i])

    def process(self, text):
        return self.trigram[self.bigram[tokenize(text)]]

    def docs(self):
        for _, doc in self.indexed_docs():
            yield self.process(doc)

    def indexed_docs(self):
        with open(self.document_path,'rb') as fin:
            for line in fin:
                if line.strip().count('\t') == 1 and line.count(' ') > 1:
                    i, doc = line.decode('utf-8',errors='replace').strip().split('\t')
                    yield i, doc

    def train_phraser(self):
        print("\t\tTraining bigram detector...")
        self.bigram = Phraser(Phrases(self.docs(), min_count=5, threshold=10, max_vocab_size=100000))
        print("\t\tTraining trigram detector...")
        self.trigram = Phraser(Phrases(self.bigram[self.docs()], min_count=5, threshold=10, max_vocab_size=100000))

    def save_phraser(self, directory):
        print("\tSaving gram detector...")
        if not os.path.isdir(directory):
            os.makedirs(directory)
        self.bigram.save(directory+'/bigrams.pkl')
        self.trigram.save(directory+'/trigrams.pkl')

    def load_phraser(self, directory):
        print("\tLoading gram detector...")
        self.bigram = Dictionary.load(directory+'/bigrams.pkl')
        self.trigram = Dictionary.load(directory+'/trigrams.pkl')

    def train_dictionary(self):
        print("\tBuilding dictionary...")
        self.dictionary = Dictionary(self.docs(), prune_at=2000000)
        self.dictionary.filter_extremes(no_below=3, no_above=0.5, keep_n=100000)

    def save_dictionary(self, directory):
        print("\tSaving dictionary...")
        if not os.path.isdir(directory):
            os.makedirs(directory)
        self.dictionary.save(directory+'/dictionary.dict')
        self.dictionary.save_as_text(directory+'/word_list.tsv')

    def load_dictionary(self, directory):
        print("\tLoading dictionary...")
        self.dictionary = Dictionary.load(directory+'/dictionary.dict')