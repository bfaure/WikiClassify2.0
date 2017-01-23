import os
from gensim import corpora
from gensim.models.ldamodel import LdaModel # single-core LDA model package

import sys
version = 2
if str(sys.version).split('.')[0] == "3":
	version = 3

'''
# constructor estimates LDA model parameters based on training corpus
lda = LdaModel(corpus, num_topics=10)

# infer topic distributions on new, unseen documents
doc_lda = lda[doc_bow]

# train model (update) w/ new documents via
lda.update(other_corpus)

# model persistency can be achieved through its load/save methods
'''

# helper for remove_stopwords
def get_words(s,stop_words):
    s = s.lower()
    s = s.replace('.', ' . ')
    s = s.replace(',', ' ,')
    s = s.replace(':', ' :')
    s = s.replace(';', ' ;')
    s = s.replace('(', '( ')
    s = s.replace(')', ' )')
    s = s.replace('-', ' - ')
    s = s.replace('"', ' "')
    s = s.replace("'", " '")
    s = s.split()

    keep = []
    for item in s:
    	if item not in stop_words:
    		keep.append(item)
    return keep

# helper for remove_stopwords
def load_stopwords():
	f = open("stopwords","r")
	text = f.read()
	words = text.split('\n')
	print("Using "+str(len(words))+" stopwords.")
	return words 

# loads each file in directory into a string, puts these strings into
# a list and returns that list.
def load_documents_from_directory(path):
	print("Loading documents from "+path)
	elems = os.listdir(path)
	documents = []
	for elem in elems:
		if os.path.isfile(path+elem):
			f = open(path+elem,'r',encoding='utf8') if version==3 else open(path+elem,'r')
			text = f.read()
			documents.append(text)
	print("Found "+str(len(documents))+" documents.")
	return documents

# prints out the topics for an lda model
def print_model_topics(LDA_model,num_topics=10):
	items = LDA_model.print_topics(num_topics)
	num = 0
	for item in items:
		print("Topic #"+str(num)+":",item)
		num+=1

def main():
	path_to_data = "data/output"
	documents = load_documents_from_directory(path_to_data)

	dictionary = corpora.Dictionary(texts)
	#dictionary.save('text.txtdic')
	corpus = [dictionary.doc2bow(text) for text in texts]

	num_topics = 10
	lda = LdaModel(corpus=corpus,id2word=dictionary,num_topics=num_topics,update_every=1,chunksize=1000,passes=1)
	print_model_topics(lda,num_topics)

	print("Done.")




if __name__ == '__main__':
	main()

