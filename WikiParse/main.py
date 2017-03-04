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

#                          Corpus wrapper class
#-----------------------------------------------------------------------------#

class wiki_corpus(object):

    def __init__(self, corpus_name, corpus_directory):
        print("Initializing '%s' corpus..." % corpus_name)

        self.name = corpus_name
        self.meta_directory = corpus_directory+'/meta'
        self.data_directory = corpus_directory+'/data'
        if not os.path.isfile(self.data_directory+'/article_revision_text.txt'):
            self.parse()
        else:
            print("\tAlready parsed!")

    def get_doc_iter(self, mode):
        if mode =='words':
            return self.get_revision_words()
        elif mode == 'categories':
            return self.get_revision_categories()
        elif mode == 'cited_authors':
            return self.get_revision_cited_authors()
        elif mode == 'cited_domains':
            return self.get_revision_cited_domains()

    def get_revision_titles(self):
        revision_map, title_map = {}, {}
        print('Fetching article titles...')
        with open(self.data_directory+'/article_titles.txt') as f:
            for line in f:
                i, j = line.strip().split('\t')
                title_map[i] = j
        print('Fetching article revisions...')
        with open(self.data_directory+'/article_revisions.txt') as f:
            for line in f:
                i, j = line.strip().split('\t')
                try:
                    revision_map[i] = title_map[j]
                except:
                    continue
        return revision_map

    def get_revision_words(self):
        text = text_corpus(self.data_directory+'/article_revision_text.txt')
        if not os.path.isfile(self.meta_directory+'/dictionary.dict'):
            text.train()
            text.save(self.meta_directory)
        else:
            text.load(self.meta_directory)
        return text

    def get_revision_categories(self):
        return category_corpus(self.data_directory+'/article_revision_categories.txt')

    def get_revision_cited_authors(self):
        return category_corpus(self.data_directory+'/article_revision_cited_authors.txt')

    def get_revision_cited_domains(self):
        return category_corpus(self.data_directory+'/article_revision_cited_domains.txt')

    def get_dump_dates(self):
        url  = 'https://dumps.wikimedia.org/%s/' % self.name
        tree = html.fromstring(requests.get(url).text)
        return [x[:-1] for x in sorted(tree.xpath('//a/@href'))[1:-1]]

    def get_dump_urls(self):
        dump_urls = []
        url  = 'https://dumps.wikimedia.org/%s/' % self.name
        for date in self.get_dump_dates():
            dump_date_text = requests.get(url+date).text
            in_progress = 'in progress' in dump_date_text or 'Partial dump' in dump_date_text
            if not in_progress:
                dump_url = '{0}{1}/{2}-{1}-pages-meta-current.xml.bz2'.format(url,date,self.name)
                dump_urls.append(dump_url)
        return dump_urls

    def parse(self):
        compiled = self.compile_parser(recompile=True)
        if not compiled:
            print("\tCould not compile parser!")
            return
        else:
            prev_date = '20010115'
            for date, dump_url in zip(self.get_dump_dates(),self.get_dump_urls()):
                date_directory = self.data_directory+'/'+date
                dump_path = download(dump_url, date_directory)
                dump_path = expand_bz2(dump_path)
                self.run_parser(dump_path, self.data_directory, prev_date)
                prev_date = date

    def compile_parser(self, recompile=False):
        print("\tCompiling parser...")
        if recompile and os.path.isfile('wikiparse.out'):
            os.remove('wikiparse.out')
        if not os.path.isfile('wikiparse.out'):
            try:
                call(["g++","--std=c++11","-O3"]+["WikiParse/code/"+x for x in ["main.cpp","wikidump.cpp","wikipage.cpp","wikitext.cpp","string_utils.cpp"]]+["-o","wikiparse.out"])
            except:
                return False
        else:
            print("\t\tParser already compiled.")
        return True

    def run_parser(self, dump_path, output_directory, prev_date):
        print("\tRunning parser...")
        call(["./wikiparse.out", dump_path, output_directory, prev_date])

#                      Tagged Document iterator
#-----------------------------------------------------------------------------#

class text_corpus(object):

    def __init__(self, document_path):
        self.document_path  = document_path
        self.instances = sum(1 for line in open(self.document_path))

    def __iter__(self):
        for i, doc in self.indexed_docs():
            yield TaggedDocument(self.trigram[self.bigram[doc]],[i])

    def process(self, text):
        return self.trigram[self.bigram[tokenize(text)]]

    def docs_phrased(self):
        for doc in self.docs():
            yield self.trigram[self.bigram[doc]]

    def docs(self):
        for _, doc in self.indexed_docs():
            yield doc

    def indexed_docs(self):
        with open(self.document_path,'rb') as fin:
            for line in fin:
                if line.strip().count('\t') == 1:
                    i, doc = line.decode('utf-8',errors='replace').strip().split('\t')
                    doc = tokenize(doc)
                    if len(doc) > 1:
                        yield i, doc

    # Phrase methods

    def save(self, directory):
        print("\tSaving gram detector...")
        check_directory(directory)
        self.bigram.save(directory+'/bigrams.pkl')
        self.trigram.save(directory+'/trigrams.pkl')

        print("\tSaving dictionary...")
        self.dictionary.save(directory+'/dictionary.dict')
        self.dictionary.save_as_text(directory+'/word_list.tsv')

    def load(self, directory):
        print("\tLoading gram detector...")
        self.bigram = Dictionary.load(directory+'/bigrams.pkl')
        self.trigram = Dictionary.load(directory+'/trigrams.pkl')

        print("\tLoading dictionary...")
        self.dictionary = Dictionary.load(directory+'/dictionary.dict')

    # Dictionary methods

    def train(self):

        print("\t\tTraining bigram detector...")
        self.bigram = Phraser(Phrases(self.docs(), min_count=5, threshold=10, max_vocab_size=100000))
        print("\t\tTraining trigram detector...")
        self.trigram = Phraser(Phrases(self.bigram[self.docs()], min_count=5, threshold=10, max_vocab_size=100000))

        print("\tBuilding dictionary...")
        self.dictionary = Dictionary(self.docs_phrased(), prune_at=2000000)
        self.dictionary.filter_extremes(no_below=3, no_above=0.5, keep_n=100000)

    def get_word_map(self):
        print("\tGetting word map...")
        return dict((v,k) for k,v in self.dictionary.token2id.iteritems())

#    # Category methods
#
#    def get_category_names(self):
#        return [self.category_map[i] for i in sorted(self.category_map.keys())]
#
#    def get_doc_categories(self, limit=-1):
#        print("\tLoading classes...")
#        categories = []
#        for i,category in enumerate(self.docs.categories()):
#            categories.append(category)
#            if i == limit:
#                break
#        mlb = MultiLabelBinarizer(classes=self.category_map.keys())
#        return mlb.fit_transform(np.array(categories))


class category_corpus(object):

    def __init__(self, document_path):
        self.document_path  = document_path
        self.instances = sum(1 for line in open(self.document_path))

    def __iter__(self):
        for i, doc in self.indexed_docs():
            yield TaggedDocument(doc,[i])

    def docs(self):
        for _, doc in self.indexed_docs():
            yield doc

    def indexed_docs(self):
        with open(self.document_path) as fin:
            for line in fin:
                if line.strip().count('\t') == 1 and line.count(' ') > 1:
                    i, doc = line.strip().split('\t')
                    doc = doc.split(' ')
                    if len(doc) > 1:
                        yield i, doc

#                             Global functions
#-----------------------------------------------------------------------------#

def build_mapping(tsv_path):
    mapping = {}
    with open(tsv_path) as f:
        for line in f:
            values = line.strip().split('\t')
            if len(values) == 2:
                key, value = values
                mapping[key] = value
    return mapping

def tokenize(text):
    return re.split('\W+', utils.to_unicode(text).lower())

def check_directory(directory):
    if not os.path.isdir(directory):
        print("\t\tCreating '%s' directory..." % directory)
        os.makedirs(directory)

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