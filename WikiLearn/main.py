import os

from code.read      import download_tarball, parse_dataset, corpus
from code.vectorize import LDA, doc2vec
from code.classify  import vector_classifier
from code.evaluate  import plot_confusion_matrix

def main():
    imdb = "https://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz"
    for dataset in [imdb]:
        dataset_name = download_tarball(dataset)
        parse_dataset(dataset_name)
        documents = get_documents(dataset_name)
        classes   = [x[1] for x in documents.classes]
        if True:
            encoder = get_LDA_model(documents, dataset_name)
            classifier = get_classifier(documents,dataset_name,'LDA')
            y_test = documents.get_classes()
            y_pred = classifier.get_classes(encoder.encode_docs())
            plot_confusion_matrix(y_test, y_pred, classes)
        if False:
            encoder = get_word2vec_model(documents, dataset_name)
            classifier = get_classifier(documents,dataset_name,'word2vec')
            y_test = documents.get_classes()
            y_pred = classifier.get_classes(encoder.get_vectors())
            plot_confusion_matrix(y_test, y_pred, classes)

def get_documents(dataset_name, model_save_directory='data/models'):
    documents = corpus(dataset_name)
    if not os.path.exists(model_save_directory+'/'+dataset_name+'/tokenizer'):
        documents.train_phrases()
        documents.save_phrases()
        documents.train_dictionary()
        documents.save_dictionary()
    else:
        documents.load_phrases()
        documents.load_dictionary()
    return documents

def get_LDA_model(documents, dataset_name, model_save_directory='data/models'):
    encoder = LDA(documents, model_save_directory)
    if not os.path.exists(model_save_directory+'/'+dataset_name+'/LDA'):
        encoder.build()
        encoder.train()
        encoder.save()
    else:
        encoder.load()
    return encoder

def get_word2vec_model(documents, dataset_name, model_save_directory='data/models'):
    encoder = doc2vec(documents, model_save_directory)
    if not os.path.exists(model_save_directory+'/'+dataset_name+'/word2vec'):
        encoder.build()
        encoder.train()
        encoder.save()
    else:
        encoder.load()
    return encoder

def get_classifier(documents, dataset_name, vector_type, model_save_directory='data/models'):
    classifier = vector_classifier(documents, model_save_directory, vector_type)
    if not os.path.exists(model_save_directory+'/'+dataset_name+'/classifier/word2vec'):
        classifier.train(encoder.get_vectors(), documents.get_classes())
        classifier.save()
    else:
        classifier.load()
    return classifier

if __name__ == "__main__":
    main()