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
    doc_ids = dict([x.strip().split('\t') for x in open('titles.tsv')])

    encoder = get_encoder('text.tsv',True,encoder_directory+'/text',300,10,5,20,10)
    save_related_tokens(encoder, 'output/related_tokens/words.tsv')
    save_related_docs(encoder, 'output/related_docs/by_words.tsv')
    save_doc_strings(doc_ids, 'output/related_docs/by_words.tsv', 'output/related_docs_(readable)/by_words.tsv')

    encoder = get_encoder('categories.tsv',False,encoder_directory+'/categories',200,300,1,5,20)
    save_related_tokens(encoder, 'output/related_tokens/categories.tsv')
    save_doc_strings(doc_ids, 'related_categories.tsv', 'related_categories_titles.tsv')
    save_related_docs(encoder, 'output/related_docs/by_categories.tsv')
    save_doc_strings(doc_ids, 'output/related_docs/by_categories.tsv', 'output/related_docs_(readable)/by_categories.tsv')

    encoder = get_encoder('links.tsv',False,encoder_directory+'/links',400,500,1,5,20)
    save_related_tokens(encoder, 'output/related_tokens/links.tsv')
    save_doc_strings(doc_ids, 'related_links.tsv', 'related_links_titles.tsv')
    save_related_docs(encoder, 'output/related_docs/by_links.tsv')
    save_doc_strings(doc_ids, 'output/related_docs/by_links.tsv', 'output/related_docs_(readable)/by_links.tsv')


def save_related_tokens(encoder, path):
    print('Saving related tokens...')
    directory = os.path.dirname(path)
    if not os.path.isdir(directory):
        os.makedirs(directory)
    with open(path,'w+') as f:
        for word in encoder.model.index2word:
            nearest = encoder.get_nearest_word(word)
            f.write(word+'\t'+'\t'.join(nearest)+'\n')

def save_related_docs(encoder, path):
    print('Saving related docs...')
    directory = os.path.dirname(path)
    if not os.path.isdir(directory):
        os.makedirs(directory)
    with open(path,'w+') as f:
        for doc_id in encoder.model.docvecs.offset2doctag:
            nearest = encoder.get_nearest_doc(doc_id)
            f.write(doc_id+'\t'+'\t'.join(nearest)+'\n')

def save_doc_strings(doc_ids, old_tsv_path, new_tsv_path):
    print('Making file human readable...')
    directory = os.path.dirname(new_tsv_path)
    if not os.path.isdir(directory):
        os.makedirs(directory)
    with open(new_tsv_path,'w+') as g:
        with open(old_tsv_path) as f:
            for x in f:
                for y in x.strip().split('\t'):
                    try:
                        g.write('%s\t' % doc_ids[y])
                    except:
                        pass
                g.write('\n')

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
    if os.path.isfile('text.tsv'):
        save_related()

if __name__ == "__main__":
    main()