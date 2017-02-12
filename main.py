#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os, sys, time

#                            Local imports
#-----------------------------------------------------------------------------#

from WikiParse.main           import corpus
from WikiLearn.code.vectorize import LDA, doc2vec
from WikiExtras.code.emailer  import send_email

#                            Main function
#-----------------------------------------------------------------------------#

def main():

    email_password = ''
    if len(sys.argv) == 2:
        _, email_password = sys.argv

    corpus_name  = 'enwiki'
    run_LDA      = False
    run_word2vec = True

    corpus_directory     = 'WikiParse/data/corpora/%s' % corpus_name
    LDA_directory        = 'WikiLearn/data/models/LDA/%s' % corpus_name
    word2vec_directory   = 'WikiLearn/data/models/word2vec/%s' % corpus_name

    documents = corpus(corpus_name, corpus_directory)

    if run_LDA:
        start_time = time.time()

        encoder = LDA(documents, LDA_directory)
    
        email_subject = "LDA training finished!"
        email_body    = "Execution time:\t%0.2f hours\nAccuracy:\t\t%s" % ((time.time()-start_time)/3600, encoder.accuracy)
        send_email(email_body, email_password, email_subject)

    if run_word2vec:
        start_time = time.time()

        encoder = doc2vec(documents, word2vec_directory)
    
        email_subject = "word2vec training finished!"
        email_body    = "Execution time:\t%0.2f hours\nAccuracy:\t\t%s" % ((time.time()-start_time)/3600, encoder.accuracy)
        send_email(email_body, email_password, email_subject)

if __name__ == "__main__":
    main()