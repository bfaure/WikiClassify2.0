#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os, sys, time

#                            Local imports
#-----------------------------------------------------------------------------#

from WikiParse.main           import wiki_corpus
from WikiLearn.code.vectorize import LDA, doc2vec

#                            Main function
#-----------------------------------------------------------------------------#

corpus_name   = 'simplewiki'
run_LDA       = False
run_word2vec  = True
corpus_directory   = 'WikiParse/data/corpora/%s' % corpus_name
LDA_directory      = 'WikiLearn/data/models/LDA/%s' % corpus_name
word2vec_directory = 'WikiLearn/data/models/doc2vec/%s' % corpus_name

def save_related_tokens(doc_iter, model_name):
    encoder = doc2vec(doc_iter, word2vec_directory+'/'+model_name)
    print('Backtesting...')
    with open('related_%s_tokens.tsv' % model_name,'w+') as f:
        for word in encoder.model.index2word:
            nearest = encoder.get_nearest_word(word)
            if nearest:
                nearest = [x for x in nearest if x != word]
                f.write(word+'\t'+'\t'.join(nearest)+'\n')

def save_related_docs(doc_iter, model_name):
    encoder = doc2vec(doc_iter, word2vec_directory+'/'+model_name)
    print('Backtesting...')
    with open('related_%s_docs.tsv' % model_name,'w+') as f:
        for doc_id in encoder.model.docvecs.offset2doctag:
            nearest = encoder.get_nearest_doc(doc_id)
            f.write(doc_id+'\t'+'\t'.join(nearest)+'\n')

def main():
    documents = wiki_corpus(corpus_name, corpus_directory)
    revision_map = documents.get_revision_titles()
    save_related_tokens(documents.get_revision_words(), 'words')
    save_related_tokens(documents.get_revision_categories(), 'categories')
    save_related_tokens(documents.get_revision_cited_authors(), 'cited_authors')
    save_related_tokens(documents.get_revision_cited_domains(), 'cited_domains')
    save_related_docs(documents.get_revision_words(), 'words')
    save_related_docs(documents.get_revision_categories(), 'categories')
    save_related_docs(documents.get_revision_cited_authors(), 'cited_authors')
    save_related_docs(documents.get_revision_cited_domains(), 'cited_domains')
    for file in ['words','categories','cited_authors','cited_domains']:
        with open('related_%s_docs.tsv' % file) as f:
            for line in f:
                related = []
                for doc_id in line.strip().split('\t'):
                    try:
                        related.append(revision_map[doc_id])
                    except:
                        continue
                related = sorted(set(related), key=lambda x: related.index(x))
                if len(related):
                    with open('related_%s_titles.tsv' % file, 'a+') as g:
                        g.write('\t'.join(related)+'\n')

if __name__ == "__main__":
    main()