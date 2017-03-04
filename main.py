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

def save_related(model_name):
    documents = wiki_corpus(corpus_name, corpus_directory)

    doc_iter  = documents.get_doc_iter(model_name)
    encoder = doc2vec(doc_iter, word2vec_directory+'/'+model_name)
    if not os.path.exists(word2vec_directory+'/'+model_name):
        if model_name == 'words':
            encoder.build(features=400, context_window=10, min_count=5, sample=1e-5, negative=20)
            encoder.train(epochs=10)
        elif model_name == 'categories':
            encoder.build(features=200, context_window=50, min_count=1, sample=1e-5, negative=5)
            encoder.train(epochs=50)
        elif model_name == 'cited_authors':
            encoder.build(features=20, context_window=50, min_count=1)
            encoder.train(epochs=100)
        elif model_name == 'cited_domains':
            encoder.build(features=80, context_window=50, min_count=1)
            encoder.train(epochs=100)
        encoder.save()
    else:
        self.load()

    print('Backtesting...')
    with open('related_%s_tokens.tsv' % model_name,'w+') as f:
        for word in encoder.model.index2word:
            nearest = encoder.get_nearest_word(word)
            if nearest:
                nearest = [x for x in nearest if x != word]
                f.write(word+'\t'+'\t'.join(nearest)+'\n')

    print('Backtesting...')
    with open('related_%s_docs.tsv' % model_name,'w+') as f:
        for doc_id in encoder.model.docvecs.offset2doctag:
            nearest = encoder.get_nearest_doc(doc_id)
            f.write(doc_id+'\t'+'\t'.join(nearest)+'\n')

    revision_map = documents.get_revision_titles()
    with open('related_%s_docs.tsv' % model_name, 'w+') as f:
        for line in f:
            related = []
            for doc_id in line.strip().split('\t'):
                try:
                    related.append(revision_map[doc_id])
                except:
                    continue
            related = sorted(set(related), key=lambda x: related.index(x))
            if len(related):
                with open('related_%s_titles.tsv' % model_name, 'a+') as g:
                    g.write('\t'.join(related)+'\n')

def main():
    for word_type in ['words','categories','cited_authors','cited_domains']:
        save_related(word_type)

if __name__ == "__main__":
    main()