import os

from code.read import download_dataset, parse_dataset, corpus
from code.vectorize import LDA, doc2vec
from code.classify  import vector_classifier

def main():

    model_save_directory = 'data/models'
    run_LDA      = True
    run_word2vec = False

    # Dataset urls
    reuters = "https://archive.ics.uci.edu/ml/machine-learning-databases/reuters21578-mld/reuters21578.tar.gz"
    imdb = "https://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz"
    twenty_newsgroups = "http://qwone.com/~jason/20Newsgroups/20news-18828.tar.gz"
    
    for dataset in [imdb]:

        dataset_name = download_dataset(dataset)
        parse_dataset(dataset_name)

        if run_LDA or run_word2vec:

            documents = corpus(dataset_name)
            if not os.path.exists(model_save_directory+'/'+dataset_name+'/tokenizer'):
                documents.train_phrases()
                documents.save_phrases()
                documents.train_dictionary()
                documents.save_dictionary()
            else:
                documents.load_phrases()
                documents.load_dictionary()
    
            if run_LDA:
                encoder = LDA(documents, model_save_directory)
                if not os.path.exists(model_save_directory+'/'+dataset_name+'/LDA'):
                    encoder.build()
                    encoder.train()
                    encoder.save()
                else:
                    encoder.load()
    
            if run_word2vec:
                encoder = doc2vec(documents, model_save_directory)
                if not os.path.exists(model_save_directory+'/'+dataset_name+'/word2vec'):
                    encoder.build()
                    encoder.train()
                    encoder.save()
                else:
                    encoder.load()

            classifier = vector_classifier(documents, model_save_directory)
            if not os.path.exists(model_save_directory+'/'+dataset_name+'/classifier'):
                classifier.train(encoder.encode_docs(), documents.get_classes())
                classifier.save()
            else:
                classifier.load()

if __name__ == "__main__":
    main()