#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import sys, time

#                            Local imports
#-----------------------------------------------------------------------------#

#from WikiParse.code.parse     import ?

from WikiLearn.code.read      import corpus
from WikiLearn.code.vectorize import LDA
from WikiLearn.code.vectorize import doc2vec

from WikiExtras.code.emailer  import send_email

#                            Main function
#-----------------------------------------------------------------------------#

def main():

    email_password = ''
    if len(sys.argv) == 2:
        _, email_password = sys.argv

    dump_path        = 'WikiParse/data/input/simplewiki-20170101-pages-articles-multistream.xml'
    database_path    = 'WikiParse/data/output/documents.json'
    models_directory = 'WikiLearn/models'

    parse_dump     = False
    train_LDA      = False
    train_word2vec = False

    ############       Parse dump       ###################
    if parse_dump:
        # Use some method defined in parse.py
        pass
    
    ############ Learn from parsed dump ###################
    if train_LDA or train_word2vec:
        documents      = corpus(database_path)
        if train_LDA:
            start_time = time.time()
            encoder = LDA(documents, 'models')
    
            email_subject = "LDA training finished!"
            email_body    = "Execution time:\t%0.2f hours\nAccuracy:\t\t%s" % ((time.time()-start_time)/3600, "Unknown")
            send_email(email_body, email_password, email_subject)
    
        if train_word2vec:
            start_time = time.time()
            encoder  = doc2vec(documents, 'models')
    
            email_subject = "word2vec training finished!"
            email_body    = "Execution time:\t%0.2f hours\nAccuracy:\t\t%s" % ((time.time()-start_time)/3600, "Unknown")
            send_email(email_body, email_password, email_subject)

if __name__ == "__main__":
    main()