#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os, sys, time

#                            Local imports
#-----------------------------------------------------------------------------#

from WikiParse.main           import download_wikidump, parse_wikidump, gensim_corpus
from WikiLearn.code.vectorize import LDA, doc2vec

#                            Main function
#-----------------------------------------------------------------------------#

def save_related():

    encoder_directory = 'WikiLearn/data/models/tokenizer'

    encoder = get_encoder('text.tsv',True,encoder_directory+'/text',400,10,5,20,10)
    save_related_tokens(encoder, 'related_authors.tsv')
    save_related_docs(encoder, 'related_docs_authors.tsv')

    encoder = get_encoder('categories.tsv',False,encoder_directory+'/categories',200,50,1,5,20)
    save_related_tokens(encoder, 'related_authors.tsv')
    save_related_docs(encoder, 'related_docs_authors.tsv')

    encoder = get_encoder('links.tsv',False,encoder_directory+'/links',200,50,2,5,20)
    save_related_tokens(encoder, 'related_authors.tsv')
    save_related_docs(encoder, 'related_docs_authors.tsv')

    encoder = get_encoder('authors.tsv',False,encoder_directory+'/authors',20,50,1,1,50)
    save_related_tokens(encoder, 'related_authors.tsv')
    save_related_docs(encoder, 'related_docs_authors.tsv')

    encoder = get_encoder('domains.tsv',False,encoder_directory+'/domains',80,50,1,1,50)
    save_related_tokens(encoder, 'related_authors.tsv')
    save_related_docs(encoder, 'related_docs_authors.tsv')

def save_related_tokens(encoder, path):
    print('Saving related tokens...')
    with open(path,'w+') as f:
        for word in encoder.model.index2word:
            nearest = encoder.get_nearest_word(word)
            f.write(word+'\t\t'.join(nearest)+'\n')

def save_related_docs(encoder, path):
    print('Saving related docs...')
    with open(path,'w+') as f:
        for doc_id in encoder.model.docvecs.offset2doctag:
            nearest = encoder.get_nearest_doc(doc_id)
            f.write(doc_id+'\t\t'.join(nearest)+'\n')

def get_encoder(tsv_path, make_phrases, directory, features, context_window, min_count, negative, epochs):
    documents = gensim_corpus(tsv_path,directory,make_phrases)
    encoder = doc2vec(documents, directory)
    if not os.path.isfile(os.path.join(directory,'word2vec.d2v')):
        encoder.build(features, context_window, min_count, negative)
        encoder.train(epochs)
        encoder.save(directory)
    else:
        encoder.load(directory)
    return encoder

def main():
    if not os.path.isfile('text.tsv'):
        dump_path = download_wikidump('simplewiki','WikiParse/data/corpora/simplewiki/data')
        parse_wikidump(dump_path)
    save_related()

if __name__ == "__main__":
    main()