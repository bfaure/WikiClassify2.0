import os

from code.read import corpus
from code.vectorize import LDA, doc2vec

def main():

    run_LDA      = False
    run_word2vec = True
    corpus_name  = 'imdb'

    corpus_directory     = 'data/corpora/%s' % corpus_name
    LDA_directory        = 'data/models/LDA/%s' % corpus_name
    word2vec_directory   = 'data/models/word2vec/%s' % corpus_name

    documents = corpus(corpus_name, corpus_directory)
    if run_LDA:
        encoder = LDA(documents, LDA_directory)
    if run_word2vec:
        encoder = doc2vec(documents, word2vec_directory)

if __name__ == "__main__":
    main()