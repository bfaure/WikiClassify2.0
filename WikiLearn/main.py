import os

from code.read      import download_tarball, parse_dataset, corpus
from code.vectorize import LDA, doc2vec
from code.classify  import vector_classifier
from code.evaluate  import plot_confusion_matrix, evaluate

def main():
    imdb = "https://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz"
    for dataset in [imdb]:
        dataset_name = 'politics'#download_tarball(dataset)
        parse_dataset(dataset_name)
        documents = get_documents(dataset_name)
        classes   = documents.get_class_names()
        if False:
            encoder = get_LDA_model(documents, dataset_name)
            X = encoder.encode_docs()
            y = documents.get_classes()
            classifier = get_classifier(documents,dataset_name,'LDA')
            y_pred = classifier.get_classes(encoder.encode_docs())
            evaluate(y_test, y_pred, classes)
        if True:
            encoder = get_word2vec_model(documents, dataset_name)
            X = encoder.get_vectors()
            y = documents.get_classes()
            classifier = get_classifier(X, y, dataset_name,'word2vec')
            y_pred = classifier.get_classes(encoder.get_vectors())
            print(evaluate(y, y_pred, classes))

def get_documents(dataset_name, model_save_directory='data/models'):
    if not os.path.exists(model_save_directory+'/'+dataset_name+'/tokenizer'):
        documents = corpus(dataset_name)
        documents.train_phrases()
        documents.save_phrases()
        documents.train_dictionary()
        documents.save_dictionary()
    else:
        documents = corpus(dataset_name)
        documents.load_phrases()
        documents.load_dictionary()
    return documents

def get_LDA_model(documents, dataset_name, model_save_directory='data/models'):
    if not os.path.exists(model_save_directory+'/'+dataset_name+'/LDA'):
        encoder = LDA(documents, model_save_directory)
        encoder.build()
        encoder.train()
        encoder.save()
    else:
        encoder.load()
    return encoder

def get_word2vec_model(documents, dataset_name, model_save_directory='data/models'):
    if not os.path.exists(model_save_directory+'/'+dataset_name+'/word2vec'):
        encoder = doc2vec(documents, model_save_directory)
        encoder.build()
        encoder.train()
        encoder.save()
    else:
        encoder = doc2vec(documents, model_save_directory)
        encoder.load()
    return encoder

def get_classifier(X, y, dataset_name, vector_type, model_save_directory='data/models'):
    if not os.path.exists(model_save_directory+'/'+dataset_name+'/classifier/word2vec'):
        classifier = vector_classifier(dataset_name, model_save_directory, vector_type)
        classifier.train(X, y)
        classifier.save()
    else:
        classifier = vector_classifier(dataset_name, model_save_directory, vector_type)
        classifier.load()
    return classifier

if __name__ == "__main__":
    main()