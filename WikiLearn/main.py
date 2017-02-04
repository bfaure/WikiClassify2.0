import os

from code.read import download_dataset, parse_dataset, corpus
from code.vectorize import LDA, doc2vec
from code.classify  import vector_classifier
from code.evaluate  import plot_confusion_matrix

def main():

    model_save_directory = 'data/models'
    run_LDA      = False
    run_word2vec = True

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

                classifier = vector_classifier(documents, model_save_directory, 'LDA')
                if not os.path.exists(model_save_directory+'/'+dataset_name+'/classifier/LDA'):
                    classifier.train(encoder.get_vectors(), documents.get_classes())
                    classifier.save()
                else:
                    classifier.load()
    
            if run_word2vec:
                encoder = doc2vec(documents, model_save_directory)
                if not os.path.exists(model_save_directory+'/'+dataset_name+'/word2vec'):
                    encoder.build()
                    encoder.train()
                    encoder.save()
                else:
                    encoder.load()

                classifier = vector_classifier(documents, model_save_directory, 'word2vec')
                if not os.path.exists(model_save_directory+'/'+dataset_name+'/classifier/word2vec'):
                    classifier.train(encoder.get_vectors(), documents.get_classes())
                    classifier.save()
                else:
                    classifier.load()

                plot_confusion_matrix(documents.get_classes(), classifier.get_classes(encoder.get_vectors()), classes=['Positive','Negative'])


if __name__ == "__main__":
    main()