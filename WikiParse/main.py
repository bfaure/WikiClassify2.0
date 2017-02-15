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

def tokenize(text):
    return re.split('\W+', utils.to_unicode(text).lower())

def check_directory(directory):
    if not os.path.isdir(directory):
        print("\t\tCreating '%s' directory..." % directory)
        os.makedirs(directory)

def expand_tar(file_path):
    print("\t\tExpanding tar...")
    if not os.path.isfile(file_path[:-7]):
        try:
            tarfile.open(file_path, 'r').extractall(os.path.dirname(file_path))
            os.remove(file_path)
        except:
            print("\t\t\tCould not expand file.")
    else:
        print("\t\t\tFile already expanded.")
    return file_path[:-7]

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
            os.remove(file_path)
        except:
            print("\t\t\tCould not expand file.")
    else:
        print("\t\t\tFile already expanded.")
    return file_path[:-4]

def download(url, directory):
    file_name = os.path.basename(urlparse(url)[2])
    file_path = directory+'/'+file_name
    print("\t\tDownloading '%s'..." % file_name)
    if not os.path.isdir(directory):
        os.makedirs(directory)
        try:
            with open(directory+'/'+file_name, "wb") as f:
                response = requests.get(url, stream=True)
                total_length = response.headers.get('content-length')
                if total_length is None: # no content length header
                    f.write(response.content)
                else:
                    dl = 0
                    total_length = int(total_length)
                    for data in response.iter_content(chunk_size=4096):
                        dl += len(data)
                        f.write(data)
                        sys.stdout.write("\r\t\t\t%0.1f%% done" % (100.0*dl/total_length))    
                        sys.stdout.flush()
                    print('')
        except:
            print("\t\t\tCould not download '%s'." % file_name)
    else:
        print("\t\t\t'%s' already exists." % file_name)
    return file_path

#                          Corpus wrapper class
#-----------------------------------------------------------------------------#

class corpus(object):

    def __init__(self, corpus_name, corpus_directory):
        print("Initializing '%s' corpus..." % corpus_name)

        self.name = corpus_name

        # Standard directories
        self.meta_directory = corpus_directory+'/meta'
        self.data_directory = corpus_directory+'/data'
        self.raw_directory  = corpus_directory+'/data/raw'

        # Standard files
        self.document_path      = self.data_directory+'/documents.tsv'
        self.category_map_path  = self.data_directory+'/category_names.tsv'
        self.category_tree_path = self.data_directory+'/category_tree.tsv'

        # Load and parse raw corpus
        if self.name == 'imdb':
            imdb_corpus(self)

        elif self.name.endswith('wiki'):
            wiki_corpus(self)

#        # Interpret categories
#        self.load_category_map()
#        self.load_category_tree()
#
#        # Create iterators from specialized classes
#        self.docs = doc_corpus(self)
#        self.bags = bag_corpus(self)
#
#        # Obtain preprocessor
#        if not os.path.exists(self.meta_directory):
#            self.train_phrases()
#            self.train_dictionary()
#            self.save_phrases()
#            self.save_dictionary()
#        else:
#            self.load_phrases()
#            self.load_dictionary()

    def process(self, text):
        tokens = [x for x in tokenize(text) if x in self.get_words()]
        return self.trigram[self.bigram[tokens]]

    # Category methods

    def load_category_map(self):
        self.category_map = {}
        with open(self.category_map_path) as fin:
            for line in fin:
                c_code, name = line.split('\t')
                self.category_map[int(c_code)] = name.strip()

    def load_category_tree(self):
        self.category_tree = {}
        with open(self.category_tree_path) as fin:
            for line in fin:
                child, parent = line.split('\t')
                parent = [int(x.strip()) for x in parent.split(',')]
                self.category_tree[int(child)] = parent

    def get_category_names(self):
        return [self.category_map[i] for i in sorted(self.category_map.keys())]

    def get_doc_categories(self, limit=-1):
        print("\tLoading classes...")
        categories = []
        for i,category in enumerate(self.docs.categories()):
            categories.append(category)
            if i == limit:
                break
        mlb = MultiLabelBinarizer(classes=self.category_map.keys())
        return mlb.fit_transform(np.array(categories))

    # Dictionary methods

    def get_word_map(self):
        print("\tGetting word map...")
        return dict((v,k) for k,v in self.dictionary.token2id.iteritems())

    def get_words(self):
        return self.dictionary.values()

    def train_dictionary(self):
        print("\tBuilding dictionary...")
        self.dictionary = Dictionary(self.docs.untagged(), prune_at=2000000)
        self.dictionary.filter_extremes(no_below=3, no_above=0.5, keep_n=100000)

    def save_dictionary(self):
        print("\tSaving dictionary...")
        check_directory(self.meta_directory)
        self.dictionary.save(self.meta_directory+'/dictionary.dict')
        self.dictionary.save_as_text(self.meta_directory+'/word_list.tsv')

    def load_dictionary(self):
        print("\tLoading dictionary...")
        self.dictionary = Dictionary.load(self.meta_directory+'/dictionary.dict')

    # Phrase methods

    def train_phrases(self):
        print("\tTraining phrases...")
        print("\t\tTraining bigram detector...")
        self.bigram = Phraser(Phrases(self.docs.docs(), min_count=5, threshold=10, max_vocab_size=100000))
        print("\t\tTraining trigram detector...")
        self.trigram = Phraser(Phrases(self.bigram[self.docs.docs()], min_count=5, threshold=10, max_vocab_size=100000))

    def save_phrases(self):
        print("\tSaving gram detector...")
        check_directory(self.meta_directory)
        self.bigram.save(self.meta_directory+'/bigrams.pkl')
        self.trigram.save(self.meta_directory+'/trigrams.pkl')

    def load_phrases(self):
        print("\tLoading gram detector...")
        self.bigram = Dictionary.load(self.meta_directory+'/bigrams.pkl')
        self.trigram = Dictionary.load(self.meta_directory+'/trigrams.pkl')

#                             Bag iterator
#-----------------------------------------------------------------------------#

class bag_corpus(object):
    def __init__(self, corpus):
        self.corpus = corpus
    def __iter__(self):
        for doc in self.corpus.docs.untagged():
            yield self.corpus.dictionary.doc2bow(doc)

#                      Tagged Document iterator
#-----------------------------------------------------------------------------#

class doc_corpus(object):
    def __init__(self, corpus):
        self.corpus = corpus
        print('\tCounting instances...')
        with open(self.corpus.document_path, 'rb') as fin:
            self.instances = sum(1 for doc in fin)

    def __iter__(self):
        for i,doc in enumerate(self.docs()):
            yield TaggedDocument(self.corpus.trigram[self.corpus.bigram[doc]],[i])
    def untagged(self):
        for doc in self.docs():
            yield self.corpus.trigram[self.corpus.bigram[doc]]
    def docs(self):
        with open(self.corpus.document_path, 'rb') as fin:
            for doc in fin:
                categories, doc = doc.split('\t')
                yield doc.split()
    def categories(self):
        with open(self.corpus.document_path, 'rb') as fin:
            for doc in fin:
                categories, doc = doc.split('\t')
                yield [int(x.strip()) for x in categories.split(',')]

#                          Wikipedia corpus
#-----------------------------------------------------------------------------#

class wiki_corpus(object):
    def __init__(self, corpus):
        self.corpus = corpus
        self.compile_parser(recompile=True)
        self.parse()
    
    def parse(self):
        for date, url in self.dump_urls():
            path = download(url, self.corpus.raw_directory+'/'+date)
            path = expand_bz2(path)
            self.run_parser(path, self.corpus.raw_directory+'/'+date)
            break

    def compile_parser(self, recompile=False):
        print("\tCompiling parser...")
        if not os.path.isfile('wikiparse.out') or recompile:
            #call(["g++","--std=c++11","-O3"]+["WikiParse/code/"+x for x in ["main.cpp","wikidump.cpp","wikipage.cpp","wikitext.cpp","string_utils.cpp"]]+["-o","wikiparse.out"])
            call(["g++","--std=c++11","-O3"]+["WikiParse/code/"+x for x in ["main.cpp","wikidump.cpp","wikipage.cpp","wikitext.cpp","string_utils.cpp"]]+["-o","wikiparse.out"])
        else:
            print("\t\tParser already compiled.")

    def run_parser(self, dump_path, output_directory):
        print("\tRunning parser...")
        call(["./wikiparse.out", dump_path, output_directory])
    
    def dump_urls(self):
        url = 'https://dumps.wikimedia.org/%s/' % self.corpus.name
        response = requests.get(url)
        tree = html.fromstring(response.text)
        dates = sorted(tree.xpath('//a/@href'),reverse=True)[1:-1]
        for date in dates:
            response = requests.get(url+date)
            if 'in progress' not in response.text:
                yield date[:-1],'{0}{1}/{2}-{1}-pages-meta-current.xml.bz2'.format(url,date[:-1],self.corpus.name)

#                             IMDb corpus
#-----------------------------------------------------------------------------#
class imdb_corpus(object):
    def __init__(self, corpus):
        self.corpus = corpus
        self.download()
        self.parse()

    def download(self):
        print("\tDownloading imdb corpus...")
        url = "https://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz"
        path = download(url, self.corpus.raw_directory)
        expand_tar(path)

    def parse(self):
        print("\tParsing dataset...")
        if not os.path.isfile(self.corpus.document_path):
            document_file      = open(self.corpus.document_path,'a+')
            category_name_file = open(self.corpus.category_map_path,'a+')
            category_tree_file = open(self.corpus.category_tree_path,'a+')
            for category, category_name in enumerate(['neg','pos']):
                category_name_file.write('%s\t%s\n' % (category,category_name))
                for subset in ['test','train']:
                    current_directory = self.corpus.raw_directory+'/aclImdb/'+subset+'/'+category_name
                    for file_name in os.listdir(current_directory):
                        if file_name.endswith('.txt'):
                            with codecs.open(current_directory+'/'+file_name,encoding='utf-8') as f:
                                doc = f.read()
                                for bad_str in ['<br />', '\n', '\t']:
                                    doc = doc.replace(bad_str, ' ')
                                document_file.write('%s\t%s\n' % (category, ' '.join(tokenize(doc))))
            document_file.close()
            category_name_file.close()
            category_tree_file.close()
        else:
            print("\t\tDataset already parsed.")