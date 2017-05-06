#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os, sys, time, random
from shutil import rmtree

# enforce auto-flushing of stdout on every write
sys.stdout = os.fdopen(sys.stdout.fileno(),'w',0) 

import numpy as np

import imageio
from keras.layers import Embedding 

import cPickle
from gensim.models.doc2vec     import TaggedDocument
#                            Local imports
#-----------------------------------------------------------------------------#
from WikiParse.main           import download_wikidump, parse_wikidump, text_corpus, item_corpus
from WikiLearn.code.vectorize import doc2vec, make_seconds_pretty
from WikiLearn.code.classify  import vector_classifier_keras

from pathfinder import get_queries, astar_path

import matplotlib.pyplot as plt 
import matplotlib.patches as patches

#                            Main function
#-----------------------------------------------------------------------------#

classification_dict = None # used by get_classified_sequences, cross-call variable
stop_words_dict     = None # used by get_classified_sequences, cross-call variable
most_common_dict    = None #
class_dict          = None 
class_pretty        = None 
classes             = None 
seen_article_dict = None # articles pulled on the last iteration, prevent repeats
# Returns the first sequences_per_class good, mid, and poor article bodies, converted to word vectors
# single sequence of word vectors returned for each article, if a start_at value is specified, will 
# traverse into the text.tsv file that far (line-wise) before starting to add documents to the data
def get_classified_sequences(  
	encoder,             # word2vec/doc2vec model wrapper
	seq_per_class,       # sequences per class to return
	min_words_per_seq,   # trim sequences w/ less than this many words
	max_words_per_seq,   # maximum words to return per sequence
	class_names,         # names to use for classes
	class_map,           # dict mapping from real classes to class_name indices
	start_at=0,                # where to pick up reading source file from
	print_avg_length=False,    # if true, print average length/class
	remove_stop_words=True,    # if true, remove stop words sequences
	trim_vocab_to=-1,          # trim any articles with less than this value in word_list.tsv (col 3)
	replace_removed=False,     # if true, any words removed will be replaced w/ zero-vector 
	swap_with_word_idx=False,  # if true, wordvectors are swapped out
	max_class_mappings=-1,      # if non -1, limit size of classification mapping
	classifications="quality.tsv", # where to pull article classifications from
	tailored_to_content=False, # diff. exec for content-classified documents
	total_seq=None, # if seq_per_class is -1, this is used to specify the number of total seqs
	multi_class_file=False # if true, class mapping file may contain multiple classes per article
	):
	
	global classification_dict # holds mappings from article_id to classification
	global stop_words_dict # holds mappings for all stop words
	global most_common_dict # holds mappings for highest frequency words
	global class_dict # holds mappings from index in class_names to class name
	global class_pretty # holds mappings from class names to formatted class names
	global classes # holds mappings from class (found in file) to index in class_names list
	global seen_article_dict # holds the last article read for each class on last iteration

	y   = [] # sequence classifications
	x   = [] # sequences

	if classes==None:
		classes = {}
		'''
		for key,val in class_map.items():
			print(key,val)
			classes[key] = np.array([class_map[key]],dtype=int)
		'''
		#for i in range(len(class_names)):
		#    classes[key]=
		pass

	longest_class_len = 0
	counts = {}
	for n in class_names:
		if len(n)>longest_class_len:
			longest_class_len = len(n)
		counts[n] = 0
	counts["unknown/not_in_model"]=0

	if seen_article_dict==None:
		seen_article_dict = {}
		for i in range(len(class_names)):
			seen_article_dict[class_names[i]]=0

	if class_dict==None:
		class_dict = {}
		for i in range(len(class_names)):
			class_dict[str(i)] = class_names[i]

	if class_pretty==None:
		class_pretty = {}
		for i in range(len(class_names)):
			class_name_pretty = class_names[i]
			while len(class_name_pretty)<=longest_class_len:
				class_name_pretty+=" "
			class_pretty[class_names[i]]=class_name_pretty

	class_lengths = {}
	for i in range(len(class_names)):
		class_lengths[i]=0

	zero_vector              = [0.00]*300 # put in place of non-modeled words
	print_sentences          = 0 # approx number of sentences to print during sentence encoding
	text                     = "text.tsv" # where to get article contents from 
	stop_words_filename      = "WikiLearn/data/stopwords/stopwords_long.txt" # source of stopwords
	word_list_filename       = "WikiLearn/data/models/dictionary/text/word_list.tsv" # source of word list

	# create stop words dictionary if not yet loaded
	if remove_stop_words and stop_words_dict==None:
		stop_words_dict = {}
		stop_words = open(stop_words_filename,"r").read().replace("\'","").split("\n")
		for s in stop_words:
			if s not in [""," "] and len(s)>0:
				stop_words_dict[s] = True

	# Create the classifications dictionary if not yet loaded
	if classification_dict==None:
		num_lines = len(open(classifications,"r").read().split("\n"))
		qf = open(classifications,"r")
		i=0
		kept=0
		num_overmapped=0
		classification_dict = {}
		for line in qf:
			i+=1
			if max_class_mappings!=-1 and i>max_class_mappings: break
			sys.stdout.write("\rCreating class dict (%d/%d) | Kept:%d | Overmapped:%d"%(i,num_lines,kept,num_overmapped))
			try:
				if multi_class_file:
					items=line.strip().split("\t")
					article_id=items[0]
					article_subclasses=items[1].split(" ")
					mapped_class=None
					overmapped=False 
					for a in article_subclasses:
						try:
							cur_mapped_class = class_map[a]
							if mapped_class==None:
								mapped_class = class_map[a]
							else:
								if cur_mapped_class!=mapped_class:
									overmapped=True 
									break 
						except:
							continue

					if overmapped==False and mapped_class!=None:
						classification_dict[article_id]=mapped_class 
						class_lengths[mapped_class]+=1
						kept+=1
					else:
						num_overmapped+=1
				else:
					article_id,article_subclass = line.strip().split("\t")
					mapped_class = class_map[article_subclass]
					classification_dict[article_id] = mapped_class
					class_lengths[mapped_class]+=1
					kept+=1
			except:
				i+=-1
				continue
		sys.stdout.write("\n")
		qf.close()

	print_class_counts=False
	if print_class_counts:
		for key,val in class_lengths.items():
			print("%s\t%d\n"%(key,val))

	class_lengths = {}
	for c in class_names:
		class_lengths[c]=0

	# if trimming vocabulary
	if ((trim_vocab_to!=-1 or swap_with_word_idx) and most_common_dict==None):
		most_common_dict = {}
		word_list = open(word_list_filename,"r").read().split("\n")
		w_idx=0
		for w in word_list:
			items = w.split("\t")
			if len(items)==3 and int(items[2])>trim_vocab_to:
				try:
					in_model = encoder.model[items[1].lower()]
					most_common_dict[items[1]]=w_idx 
					w_idx+=1
				except:
					continue

	# number of total items we will have to load (sentences or docs)
	if seq_per_class!=-1:
		approx_total = len(class_names)*seq_per_class
	else:
		approx_total = total_seq

	f = open(text,"r")
	i=0
	enc_start_time = time.time()
	num_loaded=0
	eof=True 
	earliest_class_full_at=-1 # i value when first class was filled

	# iterate over each line (document) in text.tsv
	for line in f:
		i+=1
		# skip
		if i<start_at: continue
		
		percent_done = "%0.1f%%" % (100.0*float(num_loaded+1)/float(approx_total))
		perc_loaded  = "%0.1f%%" % (100.0 *float(i)/13119700.0)
		sys.stdout.write("\rEncoding: %s done (%d/%d) | %s total | %s  "% (percent_done,num_loaded+1,approx_total,perc_loaded,make_seconds_pretty(time.time()-enc_start_time)))
		sys.stdout.flush()

		# load in the current line
		try:    
			#article_id, article_contents = line.decode('utf-8', errors='replace').strip().split('\t')
			article_id, article_contents = line.strip().split('\t')
		except: 
			continue
		
		# see if this article has a class mapping
		try: 
			art_effclass_idx = classification_dict[article_id]
			art_effclass = class_names[art_effclass_idx]
			art_eff_y = art_effclass_idx

		except: 
			# skip article if no listed quality
			counts['unknown/not_in_model'] +=1
			continue

		# skip this article if we got farther than this on the last iteration for this class
		if seen_article_dict[art_effclass]>i: continue
		
		# if we have already loaded the maximum number of articles in this category
		if seq_per_class!=-1 and counts[art_effclass]>=seq_per_class: continue
		
		# split article into sentences
		article_sentences = article_contents.split(". ")
		full_doc = []
		full_doc_str = []
		doc_arr = np.zeros(shape=(max_words_per_seq,300)).astype(float)
		# iterate over each sentence in the article
		for a in article_sentences:
			if len(full_doc)>=max_words_per_seq: break
			cleaned_a = a.replace(","," ").replace("(","").replace(")","")
			cleaned_a = cleaned_a.replace("&nbsp;","").replace("   "," ")
			cleaned_a = cleaned_a.replace("  "," ").lower()
			sentence_words = cleaned_a.split(" ")
			if remove_stop_words:
				s_idx=0
				while True:
					try:
						stop_words_dict[sentence_words[s_idx]]
						del sentence_words[s_idx]
					except:
						s_idx+=1
						if s_idx>=len(sentence_words): break

			for w in sentence_words:
				if trim_vocab_to!=-1 or swap_with_word_idx:
					try: 
						idx = most_common_dict[w.lower()]
					except: 
						if replace_removed:
							if swap_with_word_idx: full_doc.append(0)
							else: full_doc.append(zero_vector)
						continue
				try: 
					word_vec = encoder.model[w.lower()]
					if swap_with_word_idx: full_doc.append(most_common_dict[w.lower()])
					else: full_doc.append(word_vec)
					full_doc_str.append(w)
				except: 
					if replace_removed:
						if swap_with_word_idx: full_doc.append(0)
						else: full_doc.append(zero_vector)
						full_doc_str.append(w)
					continue
		# add the document
		if len(full_doc)<min_words_per_seq: continue 
		# print out doc maybe
		if random.randint(0,approx_total)<print_sentences:
			sys.stdout.write("\rExample %s sentence (decoded): %s\n"%(class_pretty[art_effclass],''.join(e+" " for e in full_doc_str[:10])+"..."))
		# populate numpy array with full_doc contents
		for q in range(len(full_doc)):
			if q==max_words_per_seq: break
			doc_arr[q,:] = full_doc[q]

		# add document/quality to total found so far
		x.append(doc_arr)
		#y.append(art_eff_y)
		y.append(art_effclass_idx)
		counts[art_effclass]+=1
		class_lengths[art_effclass]+=len(full_doc)
		num_loaded+=1 

		seen_article_dict[art_effclass]=i+1

		if seq_per_class!=-1 and counts[art_effclass]>=seq_per_class:
			if earliest_class_full_at==-1: earliest_class_full_at=i

			# check if every class has been filled 
			if min([val for _,val in counts.items()])>=seq_per_class:
				eof=False
				break

		if seq_per_class==-1:
			if len(x)>=total_seq:
				eof=False 
				break

	sys.stdout.write("\n")
	f.close()
	if print_avg_length:
		for key,value in class_lengths.iteritems():
			print("%s avg length (words): %0.1f"%(key,float(value/seq_per_class)))
		sys.stdout.write("\n")
	
	y=np.array(y)
	#y = np.ravel(np.array(y)) # flatten classifications
	X = np.array(x) # 

	if seq_per_class==-1: earliest_class_full_at=i
	if eof: earliest_class_full_at=-1 # denote eof
	return X,y,earliest_class_full_at 

# Resets all state-saving items used in get_classified_sequences
def reset_corpus():
	global seen_article_dict
	seen_article_dict=None # start classes back at start 

def make_gif(parent_folder,frame_duration=0.3):
	items = os.listdir(parent_folder)
	png_filenames = []
	for elem in items:
		if elem.find(".png")!=-1 and elem.find("heatmap")!=-1:
			png_filenames.append(elem)

	sorted_png = []
	while True:
		lowest = 10000000
		lowest_idx = -1
		for p in png_filenames:
			old_save_format=False 
			if old_save_format:
				iter_val = int(p.split("-")[2].split(":")[1])
				epoch_val = int(p.split("-")[3].split(":")[1].split(".")[0])
				val = float(iter_val)+0.1*epoch_val
			else:
				iter_val = int(p.split("-")[3].split(":")[1].split(".")[0])
				epoch_val = int(p.split("-")[2].split(":")[1])
				val = float(epoch_val)+0.1*iter_val

			if lowest_idx==-1 or val<lowest:
				lowest = val
				lowest_idx = png_filenames.index(p)

		sorted_png.append(png_filenames[lowest_idx])
		del png_filenames[lowest_idx]
		if len(png_filenames)==0: break
	png_filenames = sorted_png

	with imageio.get_writer(parent_folder+"/prediction-heatmap.gif", mode='I',duration=frame_duration) as writer:
		for filename in png_filenames:
			image = imageio.imread(parent_folder+"/"+filename)
			writer.append_data(image)

seen_article_dict = None 
def get_classified_docs(encoder,mapping_file,class_names,class_map,doc_idx,per_class):
	global seen_article_dict

	class_cts = {}
	for c in class_names:
		class_cts[class_map[c]]=0

	if seen_article_dict==None:
		seen_article_dict={}
		for c in class_names:
			seen_article_dict[class_map[c]]=0

	docvecs=[]
	ys=[]
	eof=True

	t0=time.time()
	f=open(mapping_file,"r")
	i=0
	dropped=0
	kept=0
	for line in f:
		i+=1
		perc_loaded  = "%0.1f%%" % (100.0 *float(i)/5162289.0)
		sys.stdout.write("\rEncoding: %d %s total | Kept:%d | Dropped:%d"%(i,perc_loaded,kept,dropped))
		if i<=doc_idx: continue

		items=line.strip().split("\t")
		if len(items)==2:
			try:
				item_class = class_map[items[1]]
				if seen_article_dict[item_class]>=i: continue
				if class_cts[item_class]>=per_class: continue

				article_id = items[0]
				article_vec = encoder.model.docvecs[article_id]

				docvecs.append(article_vec)
				ys.append(item_class)

				class_cts[item_class]+=1
				seen_article_dict[item_class]=i

				if min([val for _,val in class_cts.items()])>=per_class:
					eof=False 
					break
				
				kept+=1

			except:
				dropped+=1

	f.close()
	sys.stdout.write(" | %s\n"%(make_seconds_pretty(time.time()-t0)))

	X = np.array(docvecs)
	y = np.ravel(np.array(ys))

	if eof: stopped_at=-1
	else: stopped_at=i 

	return [X,y,stopped_at]

def classify_importance_docs(encoder,directory,gif=True,model_type="lstm"):
	if not os.path.exists(directory): os.makedirs(directory)

	print("\nClassifying importance on document level...\n")
	cur_time = int(time.time())
	directory = os.path.join(directory,str(cur_time))

	# all output quality classes
	class_names = ["top","high","mid","low"]
	# tagged class : index of name in class_names (to treat it as)
	class_map = {"top":0,"high":1,"mid":2,"low":3}

	class_str = ""
	for c in class_names:
		class_str+=c
		if class_names.index(c)!=len(class_names)-1: class_str+=" | "
	sys.stdout.write("Classes:\t\t%s\n"% (class_str))

	per_class = 15500
	epochs=500

	sys.stdout.write("        \t\tDocs/Iter: %d\n"%per_class)
	sys.stdout.write("        \t\tEpochs: %d\n\n"%epochs)

	classifier = vector_classifier_keras(class_names,directory)

	one_fetch=True 

	if one_fetch:
		i=1
		X,y,_ = get_classified_docs(encoder,"importance.tsv",class_names,class_map,0,5000000)

		for j in range(epochs):
			loss = classifier.train_doc_iter(X,y,iteration=i,epoch=j,plot=True)

	else:
		for j in range(epochs):
			reset_corpus()
			doc_idx=0
			i=0
			while True:
				i+=1
				print("\nEpoch:%d | Iteration: %d | doc_idx: %d"%(j,i,doc_idx))
				X,y,doc_idx = get_classified_docs(encoder,"importance.tsv",class_names,class_map,doc_idx,per_class)
				loss = classifier.train_doc_iter(X,y,iteration=i,epoch=j,plot=True,save_all=False)
				if doc_idx==-1: break 

	classifier.model.save(os.path.join(classifier.directory,"%s-classifier-last.h5"%(model_type)))
	if gif: make_gif(classifier.pic_dir)
	sys.stdout.write("\nDone\n")

def classify_importance(encoder,directory,gif=True,model_type="lstm"):
	if not os.path.exists(directory): os.makedirs(directory)

	print("\nClassifying importance by word-vector sequences...\n")
	cur_time = int(time.time())
	directory = os.path.join(directory,str(cur_time))

	# all output quality classes
	class_names = ["top","high","mid","low"]
	# tagged class : index of name in class_names (to treat it as)
	class_map = {"top":0,"high":1,"mid":2,"low":3}

	class_str = ""
	for c in class_names:
		class_str+=c
		if class_names.index(c)!=len(class_names)-1: class_str+=" | "
	sys.stdout.write("Classes:\t\t%s\n"% (class_str))

	#### SETTINGS
	#dpipc = 960
	dpipc=-1
	dpi=20000

	min_words = 2
	max_words = 1000 # maximum number of words to maintain in each document
	remove_stop_words = False # if True, removes stop words before calculating sentence lengths
	max_class_mappings = 100000 # max items to load
	limit_vocab_size = 1000 # if !=-1, trim vocab to 'limit_vocab_size' words
	batch_size = None    # if None, defaults to whats set in classify.py, requires vram
	replace_removed = True # replace words not found in model with zero vector
	swap_with_word_idx = False
	epochs=50
	####

	classifications = "importance.tsv"

	# if using CNN, this must be non -1
	if model_type=="cnn":
		if limit_vocab_size==-1:
			print("WARNING: limit_vocab_size must be non -1 for CNN")
			sys.exit(0)
		remove_stop_words=True
		swap_with_word_idx=False

	sys.stdout.write("Model Type:        \t%s\n"%model_type)
	sys.stdout.write("Max Words/Doc:     \t%d\n"%max_words)
	sys.stdout.write("Min Words/Doc:     \t%d\n"%min_words)
	sys.stdout.write("Stopwords:         \t%s\n"%("<leave>" if not remove_stop_words else "<remove>"))
	sys.stdout.write("Limit Vocab:       \t%s\n"%("<none>" if limit_vocab_size==-1 else str(limit_vocab_size)))
	sys.stdout.write("Replace Non-Model: \t%s\n"%("True" if replace_removed else "False"))
	sys.stdout.write("Swap w/ Index:     \t%s\n"%("True" if swap_with_word_idx else "False"))
	sys.stdout.write("Doc/Class/Iter:    \t%d\n\n"%dpipc)

	sys.stdout.write("Batch Size: %s\n"%("<default>" if batch_size is None else str(batch_size)))
	sys.stdout.write("Epochs:     %s\n\n"%("<default>" if epochs is None else str(epochs)))

	classifier = vector_classifier_keras(class_names=class_names,directory=directory,model_type=model_type,vocab_size=limit_vocab_size)
	last_loss=None 

	for j in range(epochs):

		reset_corpus()
		doc_idx=0
		i=0

		while True:
			i+=1
			print("\nEpoch:%d | Iteration: %d | doc_idx: %d"%(j,i,doc_idx))
			X,y,doc_idx = get_classified_sequences(    encoder, dpipc, min_words, max_words,
												class_names=class_names,
												class_map=class_map,
												start_at=doc_idx,
												remove_stop_words=remove_stop_words,
												trim_vocab_to=limit_vocab_size,
												replace_removed=replace_removed,
												swap_with_word_idx=swap_with_word_idx,
												classifications=classifications,
												max_class_mappings=max_class_mappings,
												dpi=dpi )

			loss=classifier.train_seq_iter(X,y,i,j,plot=True)
			if doc_idx==-1 or X.shape(0)<=dpi-1: break

	# write out ordered gif of all items in picture directory (heatmaps)
	if gif: make_gif(classifier.pic_dir)
	sys.stdout.write("\nReached end of text.tsv")

def classify_us_state(encoder,directory,gif=True,model_type="lstm"):
	if not os.path.exists(directory): os.makedirs(directory)
	print("Classifying U.S. states by word-vector sequences...\n")
	cur_time = int(time.time())
	directory = os.path.join(directory,str(cur_time))

	class_names_string=[]
	class_names_id=[]
	class_sizes=[]
	class_map={} 

	cat_tree=False 
	if cat_tree:
		limit=1000 
		f=open("category_children-string.tsv")

	all_classes=False
	if all_classes:
		limit=100
		# load in content category strings, ids, and counts 
		f=open("largest_categories-meta.txt","r")
		lines = f.read().split("\n")
		i=0
		for l in lines:
			i+=1
			if i>limit: break
			items=l.strip().split(" | ")
			if len(items)==3 and items[0]!="String":
				class_map[items[1]]=len(class_names_string)
				class_names_string.append(items[0])
				class_names_id.append(items[1])
				class_sizes.append(int(items[2]))
		f.close()

		i=0
		for c in class_names_string:
			sys.stdout.write("%s\t\t%s\n"%("Classes:" if i==0 else "        ",c))
			i+=1

	custom_classes=True 
	if custom_classes:

		us_states=[]
		s_f=open("us_states.txt","r")
		for line in s_f:
			line = line.strip().lower().replace(" ","_")
			if len(line)>2:
				us_states.append(line)
		s_f.close()

		class_names_string=us_states 

		class_tags=[]
		for c in class_names_string:
			class_tags.append([c])
		
		class_map={} # dict from cat id to class_name_string index to use as class 
		
		contained_classes={}
		for c in class_names_string:
			contained_classes[c]=[]
		
		class_sizes={} # number of articles in each class 
		for c in class_names_string:
			class_sizes[c]=0

		class_names_id=[]

		t0=time.time()
		#f=open("largest_categories-meta.txt","r")
		f=open("sorted_categories.tsv","r")
		lines=f.read().split("\n")
		i=0
		for l in lines:
			i+=1
			sys.stdout.write("\rMapping categories (%d/%d)"%(i,len(lines)))
			items=l.strip().split("\t")
			if len(items)==3 and items[0]!="String":
				cur_cat_str = items[0].lower()[9:]
				cur_cat_id = items[1]
				cur_cat_ct = int(items[2])

				if cur_cat_ct==0: continue # skip this cat if not articles in it
				found_class=False

				# mapping this cat to a class
				c_index=0
				for c_name,c_tags in zip(class_names_string,class_tags):
					# iterate over each tag for a match 
					for t in c_tags:
						tag_loc=cur_cat_str.find(t)

						if tag_loc!=-1:
							if tag_loc!=0: # if maybe just the end of another word (dont include)
								if cur_cat_str[tag_loc-1]!="_": 
									continue 
							if tag_loc+len(t)!=len(cur_cat_str): # if not at the end of the category string
								if cur_cat_str[tag_loc+len(t)] not in ["_","s"]: # if the beginning of another word
									continue

							if c_name=="virginia" and cur_cat_str.find("west_virginia")!=-1: continue

							found_class=True  
							class_map[cur_cat_id]=c_index
							contained_classes[c_name].append(cur_cat_str)
							class_sizes[c_name]+=cur_cat_ct 

					if found_class: break
					c_index+=1
		f.close()
		sys.stdout.write(" | %s\n"%(make_seconds_pretty(time.time()-t0)))

		i=0
		for c in class_names_string:
			contained_str=""
			q=0
			for cont in contained_classes[c]:
				q+=1
				contained_str+=cont
				if q!=len(contained_classes[c]): contained_str+=","

			sys.stdout.write("%s\t\t%d - %s\n"%("Classes:" if i==0 else "        ",class_sizes[c],c))

			print_full_classes=False
			if print_full_classes:
				sys.stdout.write("        \t%s\n"%(contained_str))
			i+=1

	#### SETTINGS
	dpipc=160
	min_words = 2
	max_words = 120 # maximum number of words to maintain in each document
	remove_stop_words = False # if True, removes stop words before calculating sentence lengths
	limit_vocab_size = 3000 # if !=-1, trim vocab to 'limit_vocab_size' words
	batch_size = None    # if None, defaults to whats set in classify.py, requires vram
	replace_removed = True # replace words not found in model with zero vector
	swap_with_word_idx = False
	epochs=100
	####

	# if using CNN, this must be non -1
	if model_type=="cnn":
		if limit_vocab_size==-1:
			print("WARNING: limit_vocab_size must be non -1 for CNN")
			sys.exit(0)
		remove_stop_words=True
		swap_with_word_idx=False

	sys.stdout.write("Model Type:        \t%s\n"%model_type)
	sys.stdout.write("Max Words/Doc:     \t%d\n"%max_words)
	sys.stdout.write("Min Words/Doc:     \t%d\n"%min_words)
	sys.stdout.write("Stopwords:         \t%s\n"%("<leave>" if not remove_stop_words else "<remove>"))
	sys.stdout.write("Limit Vocab:       \t%s\n"%("<none>" if limit_vocab_size==-1 else str(limit_vocab_size)))
	sys.stdout.write("Replace Non-Model: \t%s\n"%("True" if replace_removed else "False"))
	sys.stdout.write("Swap w/ Index:     \t%s\n"%("True" if swap_with_word_idx else "False"))
	sys.stdout.write("Doc/Class/Iter:    \t%d\n\n"%dpipc)

	sys.stdout.write("Batch Size: %s\n"%("<default>" if batch_size is None else str(batch_size)))
	sys.stdout.write("Epochs:     %s\n\n"%("<default>" if epochs is None else str(epochs)))


	classifier = vector_classifier_keras(class_names=class_names_string,directory=directory,model_type=model_type,vocab_size=limit_vocab_size)

	last_loss=None 

	# iterate over the full corpus on each iteration
	for j in range(epochs):

		reset_corpus() # tell get_classified_sequences to reset all state variables
		doc_idx = 0
		i=0
		while True:
			i+=1
			print("\nEpoch:%d | Iteration: %d | doc_idx: %d"%(j,i,doc_idx))
			X,y,doc_idx = get_classified_sequences(    encoder, dpipc, min_words, max_words,
													class_names=class_names_string,
													class_map=class_map,
													start_at=doc_idx,
													remove_stop_words=remove_stop_words,
													trim_vocab_to=limit_vocab_size,
													replace_removed=replace_removed,
													swap_with_word_idx=swap_with_word_idx,
													classifications="categories.tsv",
													multi_class_file=True )
			num_worse=0
			plot=True 
			loss = classifier.train_seq_iter(X,y,i,j,plot=plot,save_all=False)
			if doc_idx==-1: break # if at the end of the corpus

		classifier.model.save(os.path.join(classifier.directory,"%s-classifier-epoch_%d.h5"%(model_type,j)))

		if last_loss==None:
			last_loss = loss 
		elif loss>last_loss:
			print("\nLoss is increasing, ending training.\n")
			break

	# write out ordered gif of all items in picture directory (heatmaps)
	if gif: make_gif(classifier.pic_dir)
	sys.stdout.write("\nReached end of text.tsv")

def classify_content(encoder,directory,gif=True,model_type="lstm"):
	if not os.path.exists(directory): os.makedirs(directory)
	print("Classifying contents by word-vector sequences...\n")
	cur_time = int(time.time())
	directory = os.path.join(directory,str(cur_time))

	class_names_string=[]
	class_names_id=[]
	class_sizes=[]
	class_map={} # from id to index in class_names_id

	cat_tree=False 
	if cat_tree:
		limit=1000 
		f=open("category_children-string.tsv")

	all_classes=False
	if all_classes:
		limit=100
		# load in content category strings, ids, and counts 
		#f=open("largest_categories-meta.txt","r")
		f=open("sorted_categories.tsv","r")
		lines = f.read().split("\n")
		i=0
		for l in lines:
			i+=1
			if i>limit: break
			#items=l.strip().split(" | ")
			items=l.strip().split("\t")
			if len(items)==3 and items[0]!="String":
				class_map[items[1]]=len(class_names_string)
				class_names_string.append(items[0])
				class_names_id.append(items[1])
				class_sizes.append(int(items[2]))
		f.close()

		i=0
		for c in class_names_string:
			sys.stdout.write("%s\t\t%s\n"%("Classes:" if i==0 else "        ",c))
			i+=1


	# read from titles.tsv and search actual titles rather than categories here
	custom_from_titles=True
	if custom_from_titles:
		
		load=True
		if os.path.isfile("mapped-std_categories-ids.txt") and load:
			print("Loading mapped articles...")
			f=open("std_categories.txt","r")
			class_names_string=[]
			class_map={}
			class_tags=[]
			contained_classes={}

			cur_class_tags=[]
			last_line=None 
			comment=False
			for line in f:
				line=line.strip()
				if line=="/*":
					comment=True 
					continue 
				if line=="*/":
					comment=False 
					continue
				if comment:
					continue

				if last_line==None:
					#class_names_string.append(line)
					last_line=line
					continue 

				if line=="=":
					class_names_string.append(last_line)
					contained_classes[last_line]=[]
					continue
				
				if line=="]":
					class_tags.append(cur_class_tags)
					cur_class_tags=[]
					continue

				last_line=last_line.lower().replace(" ","_").replace("&","&amp;")

				for line_tag in last_line.split("/"):
					for line_tag2 in line_tag.split("&"):
						line_tag2=line_tag2.strip("_")
						#class_map[line_tag2]=len(class_names_string)-1
						contained_classes[class_names_string[-1]].append(line_tag2)
						cur_class_tags.append(line_tag2)
				last_line=line
			f.close()

			i=0
			for c in class_names_string:
				class_map[c]=i
				i+=1
		else:
			f_dest=open("mapped-std_categories.txt","w")
			f_dest_ids=open("mapped-std_categories-ids.txt","w")
			f=open("std_categories.txt","r")
			class_names_string=[]
			class_map={}
			class_tags=[]
			contained_classes={}

			cur_class_tags=[]
			last_line=None 
			comment=False
			for line in f:
				line=line.strip()
				if line=="/*":
					comment=True 
					continue 
				if line=="*/":
					comment=False 
					continue
				if comment:
					continue

				if last_line==None:
					#class_names_string.append(line)
					last_line=line
					continue 

				if line=="=":
					class_names_string.append(last_line)
					contained_classes[last_line]=[]
					continue
				
				if line=="]":
					class_tags.append(cur_class_tags)
					cur_class_tags=[]
					continue

				last_line=last_line.lower().replace(" ","_")

				for line_tag in last_line.split("/"):
					for line_tag2 in line_tag.split("&"):
						line_tag2=line_tag2.strip("_")
						#class_map[line_tag2]=len(class_names_string)-1
						contained_classes[class_names_string[-1]].append(line_tag2)
						cur_class_tags.append(line_tag2)

				last_line=line
			f.close()

			i=0
			for c in class_names_string:
				class_map[c]=i
				i+=1
				
			class_sizes={} # number of articles in each class 
			for c in class_names_string:
				class_sizes[c]=0

			class_names_id=[]

			t0=time.time()
			#f=open("largest_categories-meta.txt","r")
			f=open("titles.tsv","r")
			#f=open("sorted_categories.tsv","r")
			#lines=f.read().split("\n")
			lines=13000000
			i=0
			print_counts=True
			num_mapped=0
			for l in f:
				i+=1

				#if i>100000: break

				if print_counts:
					sys.stdout.write("\rMapping titles (%d/%d) | Mapped:%d | Counts: {"%(i,lines,num_mapped))
					for c in class_names_string:
						sys.stdout.write("%s:%d%s"%(c,class_sizes[c],", " if class_names_string.index(c)!=len(class_names_string)-1 else "}"))

				else:
					sys.stdout.write("\rMapping titles (%d/%d) | Mapped:%d"%(i,lines,num_mapped))
				items=l.strip().split("\t")
				if len(items)==2:
					cur_title_str = items[1].lower() # title of current article
					cur_title_id = items[0] # id of current article
					found_class=False

					# mapping this cat to a class
					c_index=-1
					# iterate over each class and its tags
					for c_name,c_tags in zip(class_names_string,class_tags):
						c_index+=1
						# iterate over each tag for a match 
						for t in c_tags:
							tag_loc=cur_title_str.find(t)

							if tag_loc!=-1:
								if tag_loc!=0: # if maybe just the end of another word (dont include)
									if cur_title_str[tag_loc-1]!="_": 
										continue 
								if tag_loc+len(t)!=len(cur_title_str): # if not at the end of the category string
									if cur_title_str[tag_loc+len(t)] not in ["_","s"]: # if the beginning of another word
										continue

								if found_class:
									continue

								found_class=True  
								#class_map[cur_title_id]=c_index
								f_dest.write("%s\t%s\n"%(cur_title_str,c_name))
								f_dest_ids.write("%s\t%s\n"%(cur_title_id,c_name))
								contained_classes[c_name].append(cur_title_str)
								class_sizes[c_name]+=1 

						if found_class: 
							num_mapped+=1
							break

			f.close()
			sys.stdout.write(" | %s\n"%(make_seconds_pretty(time.time()-t0)))
			f_dest.close()
			f_dest_ids.close()

			i=0
			for c in class_names_string:
				contained_str=""
				q=0
				for cont in contained_classes[c]:
					q+=1
					contained_str+=cont
					if q!=len(contained_classes[c]): contained_str+=","

				sys.stdout.write("%s\t\t%s - %d\n"%("Classes:" if i==0 else "        ",c,class_sizes[c]))

				print_full_classes=False
				if print_full_classes:
					sys.stdout.write("        \t%s\n"%(contained_str))
				i+=1


	custom_classes=False
	if custom_classes:

		avoid=["people",""]

		class_names_string=[    "arts_entertainment","automotive","business","education","family","health","food","home","law_govt_politics","news",\
								"science","sports","technoloy_computers","real_estate","shopping","religion"]


		class_targs=[   ["book","literature","celebrity","celebrities","art","entertainment","humor","movies","music","television"]      ,\
						["automotive","auto","car","convertible","coupe","crossover","diesel","vehicle","hatchback","hybrid","minivan","motorcycle","navigation","truck","wagon"]  ,\
						["business","advertising","agriculture","biotech","construction","forestry","government","human_resources","marketing","market"]    ,\
						["education",""    ]]



		class_names_string=["film","nature","music","athletics","video_game","economics","war","infrastructure_transport","politics","populated_areas","architecture"]

		class_tags=[    [ "film","television"] ,\
						[ "moth","plant","fungi","lake","beetle","animal","flora","river","lamiinae","bird","mountain","spider","calpinae","hadeninae","diptera","insect","fish","genera","fauna","beaches" ] ,\
						[ "song","single","album","musician","musical","choral"] , #singers  \
						[ "athlete","footballer","football","major_league","cricketer","cyclist","skateboarders"] ,\
						[ "video_game","virtual_reality"] ,\
						[ "companie","economic","economist"] ,\
						[ "war","air_force","paramilitary"] ,\
						[ "transport","ship","aircraft","vehicle","highway","airport","railway_station"],
						[ "politic","political","politician"],  
						[ "village","town","municipality","communities","township","school_district","populated_place","cities","suburb","boroughs"], 
						[ "skyscraper","building","houses","structures","dams","architecture"]      ]

		
		class_map={} # dict from cat id to class_name_string index to use as class 
		
		contained_classes={}
		for c in class_names_string:
			contained_classes[c]=[]
		
		class_sizes={} # number of articles in each class 
		for c in class_names_string:
			class_sizes[c]=0

		class_names_id=[]

		t0=time.time()
		f=open("largest_categories-meta.txt","r")
		#f=open("sorted_categories.tsv","r")
		lines=f.read().split("\n")
		i=0
		for l in lines:
			i+=1
			sys.stdout.write("\rMapping categories (%d/%d)"%(i,len(lines)))
			items=l.strip().split(" | ")
			if len(items)==3 and items[0]!="String":
				cur_cat_str = items[0].lower()
				cur_cat_id = items[1]
				cur_cat_ct = int(items[2])

				if cur_cat_ct==0: continue # skip this cat if not articles in it
				found_class=False

				# mapping this cat to a class
				c_index=0
				for c_name,c_tags in zip(class_names_string,class_tags):

					# iterate over each tag for a match 
					for t in c_tags:
						tag_loc=cur_cat_str.find(t)

						if tag_loc!=-1:
							if tag_loc!=9: # if maybe just the end of another word (dont include)
								if cur_cat_str[tag_loc-1]!="_": 
									continue 
							if tag_loc+len(t)!=len(cur_cat_str): # if not at the end of the category string
								if cur_cat_str[tag_loc+len(t)] not in ["_","s"]: # if the beginning of another word
									continue

							found_class=True  
							class_map[cur_cat_id]=c_index
							contained_classes[c_name].append(cur_cat_str)
							class_sizes[c_name]+=cur_cat_ct 

					if found_class: break
					c_index+=1
		f.close()
		sys.stdout.write("%s\n"%(make_seconds_pretty(time.time()-t0)))

		i=0
		for c in class_names_string:
			contained_str=""
			q=0
			for cont in contained_classes[c]:
				q+=1
				contained_str+=cont
				if q!=len(contained_classes[c]): contained_str+=","

			sys.stdout.write("%s\t\t%d - %s\n"%("Classes:" if i==0 else "        ",class_sizes[c],c))

			print_full_classes=False
			if print_full_classes:
				sys.stdout.write("        \t%s\n"%(contained_str))
			i+=1

	#### SETTINGS
	dpipc=-1
	dpi=2000
	min_words = 2
	max_words = 120 # maximum number of words to maintain in each document
	remove_stop_words = False # if True, removes stop words before calculating sentence lengths
	limit_vocab_size = -1 # if !=-1, trim vocab to 'limit_vocab_size' words
	batch_size = None    # if None, defaults to whats set in classify.py, requires vram
	replace_removed = True # replace words not found in model with zero vector
	swap_with_word_idx = False
	epochs=10
	####

	# if using CNN, this must be non -1
	if model_type=="cnn":
		if limit_vocab_size==-1:
			print("WARNING: limit_vocab_size must be non -1 for CNN")
			sys.exit(0)
		remove_stop_words=True
		swap_with_word_idx=False

	sys.stdout.write("Model Type:        \t%s\n"%model_type)
	sys.stdout.write("Max Words/Doc:     \t%d\n"%max_words)
	sys.stdout.write("Min Words/Doc:     \t%d\n"%min_words)
	sys.stdout.write("Stopwords:         \t%s\n"%("<leave>" if not remove_stop_words else "<remove>"))
	sys.stdout.write("Limit Vocab:       \t%s\n"%("<none>" if limit_vocab_size==-1 else str(limit_vocab_size)))
	sys.stdout.write("Replace Non-Model: \t%s\n"%("True" if replace_removed else "False"))
	sys.stdout.write("Swap w/ Index:     \t%s\n"%("True" if swap_with_word_idx else "False"))
	sys.stdout.write("Doc/Class/Iter:    \t%d\n\n"%dpipc)

	sys.stdout.write("Batch Size: %s\n"%("<default>" if batch_size is None else str(batch_size)))
	sys.stdout.write("Epochs:     %s\n\n"%("<default>" if epochs is None else str(epochs)))

	#classifications="categories.tsv"
	classifications="mapped-std_categories-ids.txt"

	classifier = vector_classifier_keras(class_names=class_names_string,directory=directory,model_type=model_type,vocab_size=limit_vocab_size)

	last_loss=None 

	# iterate over the full corpus on each iteration
	for j in range(epochs):

		reset_corpus() # tell get_classified_sequences to reset all state variables
		doc_idx = 0
		i=0
		while True:
			i+=1
			print("\nEpoch:%d | Iteration: %d | doc_idx: %d"%(j,i,doc_idx))
			X,y,doc_idx = get_classified_sequences(    encoder, dpipc, min_words, max_words,
													class_names=class_names_string,
													class_map=class_map,
													start_at=doc_idx,
													remove_stop_words=remove_stop_words,
													trim_vocab_to=limit_vocab_size,
													replace_removed=replace_removed,
													swap_with_word_idx=swap_with_word_idx,
													classifications=classifications,
													total_seq=dpi )
			num_worse=0
			plot=True 
			loss = classifier.train_seq_iter(X,y,i,j,plot=plot)
			if doc_idx==-1: break # if at the end of the corpus

	# write out ordered gif of all items in picture directory (heatmaps)
	if gif: make_gif(classifier.pic_dir)
	sys.stdout.write("\nReached end of text.tsv")

def classify_quality(encoder=None, directory=None, gif=True, model_type="lstm"):
	if not os.path.exists(directory): os.makedirs(directory)

	print("\nClassifying quality by word-vector sequences...\n")
	cur_time = int(time.time())
	directory = os.path.join(directory,str(cur_time))

	# all output quality classes
	class_names = ["good","mediocre","poor"]
	# tagged class : index of name in class_names (to treat it as)
	class_map = {"fa":0,"a":0,"ga":0,"bplus":0,"b":1,"c":2,"stub":2}

	# all output quality classes
	#class_names = ["featured","good","mediocre","poor"]
	# tagged class : index of name in class_names (to treat it as)
	#class_map = {"fa":0,"a":0,"ga":1,"bplus":1,"b":1,"c":2,"start":3,"stub":3}

	#class_names=["Featured","A","Good","B+","B","C","Start","Stub"]
	#class_map = {"fa":0,"a":1,"ga":2,"bplus":3,"b":4,"c":5,"start":6,"stub":7}

	#class_names=["Good","Poor"]
	#class_map = {"fa":0,"a":0,"ga":0,"bplus":0,"b":0,"c":1,"stub":1}


	class_str = ""
	for c in class_names:
		class_str+=c
		if class_names.index(c)!=len(class_names)-1: class_str+=" | "
	sys.stdout.write("Classes:\t\t%s\n"% (class_str))

	#### SETTINGS
	dpipc = 960
	min_words = 2
	max_words = 120 # maximum number of words to maintain in each document
	remove_stop_words = False # if True, removes stop words before calculating sentence lengths
	limit_vocab_size = 500 # 3000 # location at which to start allowing words in word_list.tsv
	batch_size = None    # if None, defaults to whats set in classify.py, requires vram
	replace_removed = True # replace words not found in model with zero vector
	swap_with_word_idx = False
	epochs=5
	####

	# if using CNN, this must be non -1
	if model_type=="cnn":
		if limit_vocab_size==-1:
			print("WARNING: limit_vocab_size must be non -1 for CNN")
			sys.exit(0)
		remove_stop_words=True
		swap_with_word_idx=False

	sys.stdout.write("Model Type:        \t%s\n"%model_type)
	sys.stdout.write("Max Words/Doc:     \t%d\n"%max_words)
	sys.stdout.write("Min Words/Doc:     \t%d\n"%min_words)
	sys.stdout.write("Stopwords:         \t%s\n"%("<leave>" if not remove_stop_words else "<remove>"))
	sys.stdout.write("Limit Vocab:       \t%s\n"%("<none>" if limit_vocab_size==-1 else str(limit_vocab_size)))
	sys.stdout.write("Replace Non-Model: \t%s\n"%("True" if replace_removed else "False"))
	sys.stdout.write("Swap w/ Index:     \t%s\n"%("True" if swap_with_word_idx else "False"))
	sys.stdout.write("Doc/Class/Iter:    \t%d\n\n"%dpipc)

	sys.stdout.write("Batch Size: %s\n"%("<default>" if batch_size is None else str(batch_size)))
	sys.stdout.write("Epochs:     %s\n\n"%("<default>" if epochs is None else str(epochs)))


	classifier = vector_classifier_keras(class_names=class_names,directory=directory,model_type=model_type,vocab_size=limit_vocab_size)

	last_loss=None 
	for j in range(epochs):

		reset_corpus()
		doc_idx=0
		i=0
		while True:
			i+=1
			print("\nEpoch:%d | Iteration: %d | doc_idx: %d"%(j,i,doc_idx))
			X,y,doc_idx = get_classified_sequences(    encoder, dpipc, min_words, max_words,
										class_names=class_names,
										class_map=class_map,
										start_at=doc_idx,
										remove_stop_words=remove_stop_words,
										trim_vocab_to=limit_vocab_size,
										replace_removed=replace_removed,
										swap_with_word_idx=swap_with_word_idx )
			
			loss=classifier.train_seq_iter(X,y,i,j,plot=True)
			if doc_idx==-1: break # if at end of the corpus 

	# write out ordered gif of all items in picture directory (heatmaps)
	if gif: make_gif(classifier.pic_dir)
	sys.stdout.write("\nReached end of text.tsv")

def test_classifier(classifier,encoder):
	print("\nEnter sentences to test model (q to quit)...")
	while True:
		sentence = raw_input("> ")
		print("\n")
		if sentence=="q": return

		zero_vector = [0.0]*300

		sentence.replace("."," ")
		sentence.replace(",","")
		sentence = sentence.lower()

		wordvecs = []
		for s in sentence.split():
			try:
				wordvec = encoder.model[s]
				wordvecs.append(wordvec)
			except:
				wordvecs.append(zero_vector)
		while len(wordvecs)<80:
			wordvecs.append(zero_vector)

		if len(wordvecs)>80:
			wordvecs = wordvecs[:80]

		inputs = np.array([wordvecs])
		probs = classifier.predict(inputs,batch_size=1,verbose=0)
		print(probs[0])
		plot_probabilities(probs[0],["featured","good","mediocre","poor"])

#orig_colors = [[0,73,170],[0,170,151],[34,170,0],[204,204,0],[153,0,131],[238,0,0],[238,99,0],[255,234,0]]
orig_colors = [[0,0,255],[0,0,255],[0,0,255],[0,0,255]]
def plot_probabilities(probs,labels):

	fig1 = plt.figure(figsize=(10,10),dpi=120)

	max_prob=max(probs)
	for i in range(len(probs)):
		probs[i]=probs[i]/max_prob 
		if probs[i]>1:
			probs[i]=1.0

	labels = ["featured","good","mediocre","poor"]
	colors = {}
	for l,prob in zip(labels,probs):
		cur_color = orig_colors[labels.index(l)]
		for i in range(len(cur_color)):
			cur_color[i] = float(cur_color[i])/255.0
		cur_color.append((255.0*prob/255.0))
		colors[l] = cur_color 

	ax1 = fig1.add_subplot(111,aspect='equal')
	
	loc = [0.0,0.1]
	trans_x = float(1.0/float(len(labels)))

	for l in labels:
		x,y = loc 
		#print(loc,colors[l],trans_x)
		ax1.add_patch(
			patches.Rectangle(
				(x,y), # (x,y)
				trans_x, # width
				#0.5, # width
				0.5, # height
				facecolor=colors[l],
			)
		)

		x,y = x+(trans_x/4.0),y+0.3
		ax1.annotate(l,xy=(x,y),fontsize=20)

		loc = [loc[0]+trans_x,loc[1]]

	plt.axis('off')
	plt.tight_layout()
	plt.ylabel('True label')
	plt.xlabel('Predicted label')
		
	#if save_dir!=None:
	#    plt.savefig(os.path.join(save_dir,"prediction-heatmap-%s.png"%meta),bbox_inches='tight',dpi=100)
	#    plt.close()
	#else:
	plt.show()

# returns the most recent trained model (according to naming scheme)
def get_most_recent_model(directory):
	model_dirs = os.listdir(directory)
	most_recent_model_dir = ""
	most_recent_model_time = 0 
	for m in model_dirs:
		try:
			cur_time = int(m.split("-")[0].split(":")[1])
			if cur_time>most_recent_model_time:
				most_recent_model_dir = m 
				most_recent_model_time = cur_time 
		except: continue
	return os.path.join(directory,most_recent_model_dir)

# calculates the most similar articles for all articles
def similar_articles_compiler(model_dir,topn=10,trim_under=5,start_at=0):

	preserve_prior=True
	if preserve_prior:
		log_file_strings = open("similar_articles-string-new.tsv","w")
		log_file_ids = open("similar_articles-ids-new.tsv","w")
	else:
		log_file_strings = open("similar_articles-string.tsv","w")
		log_file_ids = open("similar_articles-ids.tsv","w")

	encoder = doc2vec()
	encoder.load(model_dir)

	doctags = encoder.model.docvecs.doctags 

	title_dict = {}
	num_lines = len(open("titles.tsv","r").read().split("\n"))
	qf = open("titles.tsv","r")
	i=0
	dropped=0
	for line in qf:
		i+=1
		sys.stdout.write("\rCreating titles.tsv dict (%d/%d) Dropped: %d"%(i,num_lines,dropped))
		try:
			article_id,article_title = line.strip().split("\t")
			in_model = doctags[article_id]
			title_dict[article_id]=article_title
		except: dropped+=1

	sys.stdout.write("\n")
	qf.close()
	
	i=0
	dropped=0
	num_lines = len(doctags)

	full_ct=0
	model_time = 0
	full_start_time = time.time()
	for doctag,docinfo in doctags.items():
		full_ct+=1

		if full_ct<start_at: continue

		if (docinfo.word_count)<trim_under:
			dropped+=1
			continue

		eta_str = "ETA:"+make_seconds_pretty((num_lines)/(full_ct/(time.time()-full_start_time)))
		sys.stdout.write("\rDocs:(%d/%d) | Dropped:%d | Full:%s, Model:%s | %0.2f/s | %s"%(i,num_lines,dropped,make_seconds_pretty(time.time()-full_start_time),make_seconds_pretty(model_time),float(full_ct)/(time.time()-full_start_time),eta_str))
		sys.stdout.flush()
		try:
			a_title = title_dict[doctag]
			m0 = time.time()
			related_ids = encoder.model.docvecs.most_similar([str(doctag)],topn=topn)
			model_time += (time.time()-m0)

			log_file_strings.write("%s\t"%(a_title))
			log_file_ids.write("%s\t"%str(doctag))
			for a_id,_ in related_ids:
				log_file_ids.write("%s "%str(a_id))
				log_file_strings.write("%s "%title_dict[a_id])
			log_file_strings.write("\n")
			log_file_ids.write("\n")
			i+=1
		except:
			dropped+=1
	log_file_ids.close()
	log_file_strings.close()
	sys.stdout.write("\nDone.")
	
# parses and sends data from similar_articles-ids.tsv to server
def send_similar_articles(start_at=0,fname="similar_articles-ids.tsv"):
	if not os.path.isfile(fname):
		print("Must run similar_articles_compiler() first to create")
		print(fname+" before running send_similar_articles()")
		return

	if not os.path.isfile("titles.tsv"):
		print("titles.tsv must be present for send_similar_articles to map ")

	import psycopg2
	from psycopg2 import connect
	from bisect import bisect_left

	# connecting to database
	username = "waynesun95"
	host = "aa9qiuq51j8l7b.cja4xyhmyefl.us-east-1.rds.amazonaws.com"
	port = "5432"
	dbname = "ebdb"
	password = raw_input("Enter server password: ")

	sys.stdout.write("Trying to connect... ")
	try:
		server_conn = connect("user="+username+" host="+host+" port="+port+" password="+password+" dbname="+dbname)
	except:
		sys.stdout.write("failure\n")
		return
	sys.stdout.write("success\n")
	
	# because the first time we do this the titles will be different in similar_articles-string.tsv
	# from the titles on the server, we need to use the similar_articles-ids.tsv file and map to the
	# new titles in titles.tsv (we changed the parser so it doesn't remove '/'), normally we could just
	# use similar_articles-string.tsv and not have to maintain this titles dict in memory
	num_lines=35000000
	f=open("titles.tsv","r")
	title_dict={}
	i=0
	for line in f:
		i+=1
		sys.stdout.write("\rCreating titles dict (%d/%d)"%(i,num_lines))
		items=line.strip().split("\t")
		if len(items)==2:
			title_dict[int(items[0])]=items[1]
	f.close()
	sys.stdout.write("\n")

	article_id=[]
	similar_articles=[]
	num_lines = len(open(fname,"r").read().split("\n"))
	f=open(fname,"r")
	i=0
	for line in f:
		i+=1
		sys.stdout.write("\rMapping similar articles (%d/%d)"%(i,num_lines))
		items=line.strip().split("\t")
		if len(items)==2:
			article_id.append(items[0])
			elems=items[1].split(" ")
			similar=""
			for e in elems:
				e_str = title_dict[int(e)]
				if elems.index(e)!=len(elems)-1:
					e_str+=" | "
				similar+=e_str 
			similar_articles.append(similar)
	f.close()
	sys.stdout.write("\n")

	command_str = "UPDATE articles as t set"
	command_str+= " nearestarticles = c.nearestarticles "
	command_str+= "from (values"

	i=0
	t0=time.time()
	num_total=len(article_id)
	num_dropped=0
	sent=0
	for a_id,sim_str in zip(article_id,similar_articles):
		sim_str=sim_str.strip().replace("\'","&squot")
		i+=1

		if i<start_at: continue

		sys.stdout.write("\rPreparing server data (%d/%d) | Dropped:%d | Sent:%d"%(i,num_total,num_dropped,sent))      
		#a_imp=importance_dict[a_id]
		command = " (\'"+sim_str+"\', "+str(a_id)+")"
		command_str+=command 

		if i%5000==0 or i==num_total:
			command_str += " ) as c(nearestarticles, id) where c.id = t.id;"
			cursor=server_conn.cursor()
			cursor.execute(command_str)
			server_conn.commit()
			sent+=1

			command_str = "UPDATE articles as t set"
			command_str+= " nearestarticles = c.nearestarticles "
			command_str+= "from (values"
		else:
			command_str+=", "

	sys.stdout.write(" | %s\n"%(make_seconds_pretty(time.time()-t0)))
	sys.stdout.write("\nDone\n")

# parsers quality.tsv and importance.tsv and sends quality and importance to server
# defunct because it relies on id_mapping.tsv which we no longer use, see the new
# function send_quality_importance()
def send_quality_importance_defunct():
	
	if not os.path.isfile("id_mapping.tsv"):
		print("File id_mapping.tsv must be present to perform this task")
		return

	if not os.path.isfile("quality.tsv"):
		print("File quality.tsv must be present to perform this task")
		return

	if not os.path.isfile("importance.tsv"):
		print("File importance.tsv must be present to perform this task")
		return

	import psycopg2
	from psycopg2 import connect
	from bisect import bisect_left

	# connecting to database
	username = "waynesun95"
	host = "aa9qiuq51j8l7b.cja4xyhmyefl.us-east-1.rds.amazonaws.com"
	port = "5432"
	dbname = "ebdb"
	password = raw_input("Enter server password: ")

	sys.stdout.write("Trying to connect... ")
	try:
		server_conn = connect("user="+username+" host="+host+" port="+port+" password="+password+" dbname="+dbname)
	except:
		sys.stdout.write("failure\n")
		return
	sys.stdout.write("success\n")

	# getting all ids in the database
	cursor = server_conn.cursor()
	command = "SELECT id FROM articles"

	sys.stdout.write("Requesting all article ids... ")
	try:
		cursor.execute(command)
		data = cursor.fetchall()
	except:
		sys.stdout.write("failure\n")
		return
	sys.stdout.write("success\n")
	cursor.close()

	if data is not None:
		num_rows = len(data)
		if num_rows==0:
			print("Table is empty!")
			return
		print("Found %d rows in table" % num_rows)
	else:
		print("Data received is None!")
		return 

	# returns the real id for a given .tsv file row
	def get_real_id(row):
		return int(row.split("\t")[1])

	# opening the id_mapping.tsv file 
	print("Reading id_mapping.tsv...")
	id_mapping = open("id_mapping.tsv","r").read().split("\n")
	rows = []
	for row in id_mapping:
		items = row.split("\t")
		if len(items)==2: rows.append(row)
	print("Sorting id mappings by real id...")
	rows = sorted(rows,key=get_real_id)
	print("Splitting id mappings...")
	ids_talk = []
	ids_real = []
	for r in rows:
		items = r.split("\t")
		ids_talk.append(int(items[0]))
		ids_real.append(int(items[1]))

	# returns index of input query in ids_real list
	def binary_search(query,lo=0,hi=None):
		hi = hi or len(ids_real)
		return bisect_left(ids_real,query,lo,hi)

	# returns the talk page id for a given real page id
	def real_to_talk_id(real_page_id):
		return ids_talk[binary_search(real_page_id)]

	# opening the quality.tsv file
	print("Reading quality.tsv...")
	qual_mapping = open("quality.tsv","r").read().split("\n")
	q_rows = []
	for row in qual_mapping:
		items = row.split("\t")
		if len(items)==2: q_rows.append(row)

	# opening the importance.tsv file 
	print("Reading importance.tsv...")
	imp_mapping = open("importance.tsv","r").read().split("\n")
	i_rows = []
	for row in imp_mapping:
		items = row.split("\t")
		if len(items)==2: i_rows.append(row)

	print("Creating quality,importance dictionary...")
	qual_imp_dict = {}
	for c_q,c_i in zip(q_rows,i_rows):
		cur_id,quality = c_q.split("\t")
		o_id,importance = c_i.split("\t")
		if cur_id!=o_id:
			print("ERROR: cur_id!=o_id")
			return
		qual_imp_dict[str(cur_id)] = [quality,importance] 

	# returns the quality for a given real_article_id
	def get_quality_importance(real_article_id):
		talk_id = str(real_to_talk_id(real_article_id))
		return qual_imp_dict[talk_id]

	# iterate over all real ids in the server 
	sys.stdout.write("Processing...")
	seen_ids = []
	resp_qual = []
	resp_imp = []
	i=0
	dropped=0
	for r in data:
		i+=1
		sys.stdout.write("\rProcessing (%d/%d)   " % (i,num_rows))
		cur_id = r[0]
		try:
			qual,imp = get_quality_importance(cur_id)
			seen_ids.append(str(cur_id))
			resp_qual.append(str(qual))
			resp_imp.append(str(imp))
		except: dropped+=1
	sys.stdout.write("\n")
	if dropped>0: print("Dropped %d articles due to error" % dropped)

	# TODO: make the update buffered

	# sending all of the classification_dict and importances to the server
	sys.stdout.write("Sending to server...")
	for i in range(len(seen_ids)):
		cursor = server_conn.cursor()
		command = "UPDATE articles SET quality = \'"+resp_qual[i]+"\', importance = \'"+resp_imp[i]+"\' "
		command += "WHERE id = "+seen_ids[i]+";"
		cursor.execute(command)
		sys.stdout.write("\rSending to server (%d/%d)   " % (i,len(seen_ids)))
		cursor.close()
	server_conn.commit()
	sys.stdout.write("\n")
	print("Done")

# parses quality.tsv and importance.tsv and sends quality and importance to server
def send_quality_importance(start_at=0):

	if not os.path.isfile("quality.tsv"):
		print("File quality.tsv must be present to perform this task")
		return

	if not os.path.isfile("importance.tsv"):
		print("File importance.tsv must be present to perform this task")
		return

	import psycopg2
	from psycopg2 import connect
	from bisect import bisect_left

	# connecting to database
	username = "waynesun95"
	host = "aa9qiuq51j8l7b.cja4xyhmyefl.us-east-1.rds.amazonaws.com"
	port = "5432"
	dbname = "ebdb"
	password = raw_input("Enter server password: ")

	sys.stdout.write("Trying to connect... ")
	try:
		server_conn = connect("user="+username+" host="+host+" port="+port+" password="+password+" dbname="+dbname)
	except:
		sys.stdout.write("failure\n")
		return
	sys.stdout.write("success\n")

	t0=time.time()
	num_lines=5171609
	f=open("quality.tsv","r")
	quality_dict={}
	i=0
	for line in f:
		i+=1
		sys.stdout.write("\rCreating quality dict (%d/%d)"%(i,num_lines))
		items=line.strip().split("\t")
		if len(items)==2:
			quality_dict[int(items[0])]=items[1]
	f.close()
	sys.stdout.write(" | %s\n"%(make_seconds_pretty(time.time()-t0)))


	t0=time.time()
	f=open("importance.tsv","r")
	importance_dict={}
	i=0
	for line in f:
		i+=1
		sys.stdout.write("\rCreating importance dict (%d/%d)"%(i,num_lines))
		items=line.strip().split("\t")
		if len(items)==2:
			#print("Importance, items[0]:%s, items[1]:%s"%(items[0],items[1]))
			importance_dict[int(items[0])]=items[1]
	f.close()
	sys.stdout.write(" | %s\n"%(make_seconds_pretty(time.time()-t0)))

	command_str = "UPDATE articles as t set"
	command_str+= " quality = c.quality,"
	command_str+= " importance = c.importance "
	command_str+= "from (values"

	i=0
	t0=time.time()
	num_total=len(quality_dict)
	num_dropped=0
	sent=0
	for a_id,a_qual in quality_dict.items():
		i+=1

		if i<start_at: continue

		sys.stdout.write("\rPreparing server data (%d/%d) | Dropped:%d | Sent:%d"%(i,num_total,num_dropped,sent))      
		a_imp=importance_dict[a_id]
		command = " (\'"+a_qual+"\', \'"+a_imp+"\', "+str(a_id)+")"
		command_str+=command 

		if i%5000==0 or i==num_total:
			command_str += " ) as c(quality, importance, id) where c.id = t.id;"
			cursor=server_conn.cursor()
			cursor.execute(command_str)
			server_conn.commit()
			sent+=1

			command_str = "UPDATE articles as t set"
			command_str+= " quality = c.quality,"
			command_str+= " importance = c.importance "
			command_str+= "from (values"
		else:
			command_str+=", "

	sys.stdout.write(" | %s\n"%(make_seconds_pretty(time.time()-t0)))
	sys.stdout.write("\nDone\n")

# Either creates titles dictionary from titles.tsv or loads it (if titles.pkl exists)
def get_titles_dict():
	if not os.path.isfile("titles.pkl"):
		t0=time.time()
		i=0
		dropped=0
		title_dict={}
		f=open("titles.tsv","r")
		for line in f:
			i+=1
			sys.stdout.write("\rCreating titles dict (%d/%d) | Dropped:%d"%(i,34178963,dropped))
			items=line.strip().split("\t")
			if len(items)==2: title_dict[items[0]]=items[1]
			else: dropped+=1
		f.close()
		with open("titles.pkl","wb") as f:
			cPickle.dump(title_dict,f)
		sys.stdout.write(" | %s\n"%(make_seconds_pretty(time.time()-t0)))
		return title_dict 
	else:
		t0=time.time()
		sys.stdout.write("Loading titles dict... ")
		with open("titles.pkl","rb") as f:
			title_dict = cPickle.load(f)
		sys.stdout.write("%s\n"%(make_seconds_pretty(time.time()-t0)))
		return title_dict

# Either creates sorted_categories.tsv and returns n_largest or read n_largest from it
def get_nlargest_categories(n_largest,title_dict):

	from bisect import bisect_left # for sorting

	def get_row_size(row):
		return row[1]

	if os.path.exists("sorted_categories.tsv"):
		f=open("sorted_categories.tsv","r")
		largest_sizes=[]
		largest_ids=[]
		largest_strings=[]
		i=0
		t0=time.time()
		for line in f:
			i+=1
			sys.stdout.write("\rLoading largest cats (%d/%d)"%(i,n_largest))
			items=line.strip().split("\t")
			if len(items)==3:
				largest_strings.append(items[0])
				largest_ids.append(items[1])
				largest_sizes.append(int(items[2]))
			if len(largest_sizes)==n_largest:
				sys.stdout.write(" | %s\n"%(make_seconds_pretty(time.time()-t0)))
				f.close()
				return [largest_strings,largest_ids,largest_sizes]

	t0=time.time()
	f=open("categories.tsv","r")
	cat_size_dict={}
	i=0
	for line in f:
		i+=1
		sys.stdout.write("\rReading categories (%d/%d)"%(i,14697972))
		items=line.strip().split("\t")
		if len(items)==2:
			line_cats=items[1].split(" ")
			for l in line_cats:
				try:
					temp=cat_size_dict[l]
					cat_size_dict[l]+=1
				except: cat_size_dict[l]=0
	f.close()
	sys.stdout.write(" | %s\n"%(make_seconds_pretty(time.time()-t0)))

	num_total=len(cat_size_dict)
	rows=[]
	i=0
	t0=time.time()
	for key,val in cat_size_dict.items():
		i+=1
		sys.stdout.write("\rSorting categories (%d/%d)"%(i,num_total))
		rows.append([key,val])
	rows=sorted(rows,key=get_row_size,reverse=True)
	sys.stdout.write(" | %s\n"%(make_seconds_pretty(time.time()-t0)))

	t0=time.time()
	large_categories=[]
	large_category_sizes=[]
	large_categories_strings=[]
	f=open("sorted_categories.tsv","w")
	dropped=0
	for i in range(len(rows)):
		sys.stdout.write("\rSaving largest (%d/%d) | Dropped:%d"%(i,len(rows),dropped))
		try:
			cur_id = rows[i][0]
			cur_size = rows[i][1]
			cur_string = title_dict[cur_id]
			f.write("%s\t%s\t%d\n"%(cur_string,cur_id,cur_size))
		except:
			dropped+=1
	sys.stdout.write(" | %s\n"%(make_seconds_pretty(time.time()-t0)))
	f.close()
	return get_nlargest_categories(n_largest,title_dict) # recursive call

# parses categories.tsv
def largest_categories_compiler(n_largest=20000,smart_combine=False):

	if not os.path.isfile("categories.tsv"):
		print("categories.tsv is required to run largest_categories_compiler()")
		return

	# Load (or create) a dictionary with mappings from ids to article titles    
	title_dict = get_titles_dict()

	# get n_largest article names, ids, and sizes (# of articles)
	large_categories_strings,large_categories,large_category_sizes = get_nlargest_categories(n_largest,title_dict)

	# sizes based on the amounts of articles we will map to them
	effective_category_sizes={}

	# small category dictionaries
	cat_id_to_string_dict={}
	cat_id_to_size_dict={}
	i=0
	for p_id,p_str in zip(large_categories,large_categories_strings):
		i+=1
		sys.stdout.write("\rMapping ids to strings (%d/%d)"%(i,len(large_categories)))
		cat_id_to_string_dict[p_id]=p_str
		cat_id_to_size_dict[p_id]=large_category_sizes[i-1]
		effective_category_sizes[p_id]=0
	sys.stdout.write("\n")

	# map articles to their categories
	f_id= open("article_categories-ids.tsv","w")
	f_str = open("article_categories-string.tsv","w")
	t0=time.time()
	f=open("categories.tsv","r")
	i=0
	dropped=0
	num_saved=0
	for line in f:
		i+=1
		sys.stdout.write("\rMapping articles to categories (%d/%d) | Saved:%d | Dropped:%d"%(i,13119700,num_saved,dropped))
		items=line.strip().split("\t")
		if len(items)==2:
			line_cats=items[1].split(" ")
			cat_priority=None 
			cat_id=None 
			cat_str=None
			for l in line_cats:
				try:
					large_with_size = cat_id_to_size_dict[l]
					if cat_priority==None or int(large_with_size)<cat_priority:
						cat_str=cat_id_to_string_dict[l]
						cat_id=l 
						cat_priority=int(large_with_size)
				except: continue 
			if cat_id!=None:
				try:
					f_str.write("%s\t%s\n"%(title_dict[items[0]],cat_str))
					f_id.write("%s\t%s\n"%(items[0],cat_id))
					num_saved+=1
					effective_category_sizes[cat_id]+=1
				except:
					dropped+=1
	sys.stdout.write(" | %s\n"%(make_seconds_pretty(time.time()-t0)))
	f_id.close()
	f_str.close()

	# write out the subsection of the total sorted categories to files
	f_id = open("largest_categories-ids.tsv","w")
	f_str = open("largest_categories-string.tsv","w")
	for i in range(len(large_category_sizes)):
		sys.stdout.write("\rSaving largest (%d/%d)"%(i+1,len(large_category_sizes)))
		#c_size=large_category_sizes[i]
		c_str=large_categories_strings[i]
		c_id=large_categories[i]
		c_size=effective_category_sizes[c_id]
		f_id.write("%s\t%d\n"%(c_id,c_size))
		f_str.write("%s\t%d\n"%(c_str,c_size))
	f_id.close()
	f_str.close()
	sys.stdout.write("\n")

	sys.stdout.write("\nDone\n")

	# write out metadata (helps with prepping classifier)
	print("Writing metadata...")
	f_meta = open("largest_categories-meta.txt","w")
	f_meta.write("String | ID | Article Count\n\n")
	for i in range(len(large_categories)):
		#f_meta.write("%s | %s | %d\n"%(large_categories_strings[i],large_categories[i],large_category_sizes[i]))
		cur_id=large_categories[i]
		cur_str=large_categories_strings[i]
		f_meta.write("%s | %s | %d\n"%(cur_str,cur_id,effective_category_sizes[cur_id]))
	f_meta.close()

def get_most_recent_classifier(which,parent_dir="WikiLearn/data/models/classifier",spec=None):
	my_dir = os.path.join(parent_dir,which)
	classifiers = os.listdir(my_dir)
	most_recent = None 
	for c in classifiers:
		try:
			if most_recent==None or int(c)>int(most_recent):
				most_recent=c 
		except:
			continue 
	classifier_dir=os.path.join(my_dir,most_recent)
	if spec!=None:
		classifier_f=os.path.join(classifier_dir,"lstm-classifier-%s.h5"%spec) 
	else:
		classifier_f=os.path.join(classifier_dir,"lstm-classifier.h5") 
	from keras.models import load_model
	classifier = load_model(classifier_f)
	return classifier

# use input classifier and encoder to classify all documents in text.tsv
def generate_classifier_samples_docs(classifier,class_names,encoder,which):

	text = "text.tsv"

	max_len=120 # length of input sequences classifier was trained with
	zero_vector = [0.0]*300
	trim_under = 3000 # trim_under used when classifier was trained
	
	t0=time.time()

	f_targ=open("classified_articles-%s.txt"%which,"w")
	f_targ_floats=open("classified_articles_float-%s.txt"%which,"w")

	f_targ_floats.write("Classes\t")
	i=0
	for c in class_names:
		i+=1
		f_targ_floats.write("%s%s"%(c,"\t" if i!=len(class_names) else "\n"))

	'''
	i=0
	#f=open("titles.tsv","r").read().split("\n")
	f=open("titles.tsv","r")
	title_dict={}
	for line in f:
		i+=1
		sys.stdout.write("\rBuilding titles dict (%d/%d)"%(i,34000000))
		items=line.strip().split("\t")
		if len(items)==2:
			title_dict[items[0]]=items[1]
	sys.stdout.write("\n")
	f.close()
	'''
	
	
	i=0
	word_list_filename = "WikiLearn/data/models/dictionary/text/word_list.tsv" # source of word list
	#f=open(word_list_filename,"r").read().split("\n")
	f=open(word_list_filename,"r")
	word_dict={}
	for line in f:
		i+=1
		sys.stdout.write("\rBuilding words dict (%d/%d)"%(i,13000000))
		items=line.strip().split("\t")
		if len(items)==3 and int(items[2])>trim_under:
			try:
				in_model=encoder.model[items[1].lower()]
				word_dict[items[1]]=True
			except:
				continue
	sys.stdout.write("\n")
	f.close()
	

	#num_total=len(open(text,"r").read().split("\n"))
	num_total=13000000
	dropped=0
	kept=1
	total_len=0.0
	f=open(text,"r")
	i=0
	for line in f:
		i+=1
		sys.stdout.write("\rClassifying (%d/%d/%d) | Dropped:%d | Avg. len:%0.2f"%(kept,i+1,num_total,dropped,float(total_len/kept)))
		items=line.strip().split("\t")
		#if len(items)==2:
		try:
			article_title_id,article_contents=items[0],items[1]
			article_title_str=title_dict[article_title_id]
			#article_title_str=str(article_title_id)

			words=article_contents
			#words=article_contents.replace("."," ")
			#words=article_contents.split(" ")

			cleaned_a = a.replace(","," ").replace("(","").replace(")","")
			cleaned_a = cleaned_a.replace("&nbsp;","").replace("   "," ")
			cleaned_a = cleaned_a.replace("  "," ").lower()
			words = cleaned_a.split(" ")


			wordvecs=[]

			for w in words:
				try:
					in_dict=word_dict[w.lower()]
					try:
						encoded_word=encoder.model[w.lower()]
						wordvecs.append(encoded_word)
					except:
						wordvecs.append(zero_vector)
					if len(wordvecs)==max_len: break 
					
				except:
					continue 

			kept+=1
			total_len+=len(wordvecs)

			while len(wordvecs)<120:
				wordvecs.append(zero_vector)

			inputs=np.array([wordvecs])
			probs=classifier.predict(inputs,batch_size=1,verbose=0)

			f_targ_floats.write("%s\t"%article_title_str)

			max_prob=0.0 
			j=0
			for p in probs[0]:
				if p>max_prob:
					max_prob=p 
					pred_class=class_names[j]
				f_targ_floats.write("%0.5f%s"%(p,"\t" if j!=len(class_names)-1 else "\n"))
				f_targ_floats.flush()
				j+=1

			if max_prob!=0.0:
				f_targ.write("%s\t%s\n"%(article_title_str,pred_class))
				f_targ.flush()
			else:
				dropped+=1
		except:
			dropped+=1

	sys.stdout.write(" | %s\n"%(make_seconds_pretty(time.time()-t0)))
	sys.stdout.write("Done\n")

# use input classifier and encoder to classify all words in word_list.tsv
# save results to 20k_most_common-'which'.txt and 20k_most_common_float-'which'.txt
def generate_classifier_samples_words(classifier,class_names,encoder,which):

	text = "WikiLearn/data/models/dictionary/text/word_list.tsv"

	break_items=["nbsp","ndash","_"]

	max_len=120 # length of input sequences classifier was trained with
	trim_under_prob=0.6 #0.7 # trim word if the classifier is less confident than this

	start_tsv_at =1000000 # highest word frequency to allow (see 3rd col in word_list.tsv)
	end_tsv_at   =3000

	zero_vector = [0.0]*300
	
	t0=time.time()

	f_targ=open("20k_most_common-%s.txt"%which,"w")
	f_targ_floats=open("20k_most_common_float-%s.txt"%which,"w")

	f_targ_floats.write("Classes\t")
	i=0
	for c in class_names:
		i+=1
		f_targ_floats.write("%s%s"%(c,"\t" if i!=len(class_names) else "\n"))


	num_total=len(open(text,"r").read().split("\n"))
	dropped=0
	kept=0
	f=open(text,"r")
	i=0
	for line in f:
		i+=1
		sys.stdout.write("\rClassifying (%d/%d/%d) | Dropped:%d"%(kept,i+1,num_total,dropped))

		items=line.strip().split("\t")
		word=items[1]
		freq=int(items[2])

		if freq>start_tsv_at or freq<end_tsv_at: continue

		skip=False 
		for b in break_items:
			if word.find(b)!=-1: 
				skip=True 
				break 
		if skip: continue
		
		wordvecs=[]
		try:
			wordvec=encoder.model[word.lower()]
			wordvecs.append(wordvec)

			while len(wordvecs)<max_len:
				wordvecs.append(zero_vector)

			if len(wordvecs)>max_len:
				wordvecs=wordvecs[:max_len]

			inputs=np.array([wordvecs])
			probs=classifier.predict(inputs,batch_size=1,verbose=0)

			f_targ_floats.write("%s\t"%word)

			max_prob=trim_under_prob # anything under this not counted
			j=0
			for p in probs[0]:
				#print(p)
				if p>max_prob:
					max_prob=p 
					pred_class=class_names[j]
				f_targ_floats.write("%0.5f%s"%(p,"\t" if j!=len(class_names)-1 else "\n"))
				f_targ_floats.flush()
				j+=1
			if max_prob!=trim_under_prob:
				kept+=1
				f_targ.write("%s\t%s\n"%(word,pred_class))
				f_targ.flush()
			else:
				dropped+=1

		except:
			dropped+=1
			continue 
	sys.stdout.write(" | %s\n"%(make_seconds_pretty(time.time()-t0)))
	sys.stdout.write("Done\n")

def build_category_tree():
	if not os.path.isfile("category_parents-string.tsv"):
		title_dict={}
		i=0
		f=open("titles.tsv","r")
		for line in f:
			i+=1
			sys.stdout.write("\rMappings titles.tsv (%d/%d)"%(i,32000000))
			items=line.strip().split("\t")
			if len(items)==2:
				title_dict[int(items[0])]=items[1]
		f.close()
		sys.stdout.write("\n")

		f=open("category_parents.tsv","r")
		dest=open("category_parents-string.tsv","w")

		j=0
		dropped=0
		for line in f:
			j+=1
			sys.stdout.write("\rSaving category parents strings (%d) | Dropped:%d"%(j,dropped))
			items=line.strip().split("\t")
			try:
				for i in range(len(items)):
					dest.write("%s%s"%(title_dict[int(items[i])],"\t" if i!=len(items)-1 else "\n"))
			except:
				dropped+=1
		f.close()
		dest.close()
		sys.stdout.write("\n")

	f=open("category_parents-string.tsv","r")

	category_children={}

	i=0
	for line in f:
		i+=1
		sys.stdout.write("\rAssembling category parents %d"%i)
		items=line.strip().split("\t")
		if len(items)>1:
			for p in items[1:]:
				try:
					temp=category_children[p]
					category_children[p].append(items[0])
				except:
					category_children[p]=[items[0]]
	f.close()
	sys.stdout.write("\n")

	cat_sizes=[]
	print("Sorting categories by number of children")
	i=0
	for key,value in category_children.items():
		cat_sizes.append([key,len(value)])
		i+=1

	def get_size(row):
		return row[1]

	cat_sizes=sorted(cat_sizes,key=get_size,reverse=True)

	f=open("category_children-string.tsv","w")
	i=0
	for key,_ in cat_sizes:
		i+=1
		sys.stdout.write("\rSaving %d"%i)
		f.write("%s\t"%key)
		children=category_children[key]
		for c in children:
			f.write("%s%s"%(c," " if children.index(c)!=len(children)-1 else "\n"))
	f.close()
	sys.stdout.write("\nDone\n")

def load_standard_categories(fname="std_categories.txt"):

	if fname.find(".tsv")!=-1:
		titles=[]
		f=open(fname,"r")
		for line in f:
			items=line.strip().split("\t")
			if len(items)>1:
				titles.append(items[0])
		return titles,None

	f=open(fname,"r")
	class_names_string=[]
	class_map={}
	class_tags=[]
	contained_classes={}

	cur_class_tags=[]
	last_line=None 
	comment=False
	for line in f:
		line=line.strip()
		if line=="/*":
			comment=True 
			continue 
		if line=="*/":
			comment=False 
			continue
		if comment:
			continue
		if last_line==None:
			last_line=line
			continue 

		if line=="=":
			class_names_string.append(last_line)
			contained_classes[last_line]=[]
			continue
		
		if line=="]":
			class_tags.append(cur_class_tags)
			cur_class_tags=[]
			continue

		last_line=last_line.lower().replace(" ","_").replace("&","&amp;")

		for line_tag in last_line.split("/"):
			for line_tag2 in line_tag.split("&"):
				line_tag2=line_tag2.strip("_")
				#class_map[line_tag2]=len(class_names_string)-1
				contained_classes[class_names_string[-1]].append(line_tag2)
				cur_class_tags.append(line_tag2)
		last_line=line
	f.close()

	i=0
	for c in class_names_string:
		class_map[c]=i
		i+=1

	return class_names_string,contained_classes

def similar_interface(enc_fname,spec):
	encoder = doc2vec()
	encoder.load(enc_fname,spec)

	def title(id):
		f=open("titles.tsv","r")
		for line in f:
			if line.strip().split("\t")[0]==str(id):
				return line.strip().split("\t")[1]
		f.close()
		return "None"

	def id(title):
		f=open("titles.tsv","r")
		for line in f:
			if line.strip().split("\t")[1]==str(title):
				return line.strip().split("\t")[0]
		f.close()
		return "None"
	
	while True:
		sent = raw_input("Enter a word: ")
		if sent=="q": break 
		#word_id = title_dict[sent]
		try:
			similar=encoder.model.docvecs.most_similar(sent)
			print(similar)
		except:
			print("Not in model")

std_cat_dict=None 
def std_category_dist(query,encoder,disp=False):
	global std_cat_dict
	if std_cat_dict==None:
		std_cat_dict={}
		with open("std_categories.tsv","r") as f:
			for line in f:
				items=line.strip().split("\t")
				name=items[0]
				doc=[]
				for d in items[1].split(" "):
					if len(d)>2: doc.append(d)
				docvec=encoder.model.infer_vector(doc)
				#docvec=encoder.model[doc[0].split(" ")[0]]
				std_cat_dict[name]=docvec 

	#query_vec = encoder.model[query]
	try:
		query_vec=encoder.model.docvecs[query]
		print("INTERPRETED AS A DOCUMENT")
	except:
		try:
			query_vec=encoder.model[query]
			print("INTERPRETED AS A WORD")
		except:
			print("Query not in model")

	if disp:
		#print(query_vec)
		print(encoder.model.docvecs.most_similar([query_vec]))
		try:
			print(encoder.model.most_similar([query_vec]))
		except:
			print("Couldn't get similar words.")

	query_dist=[]
	for cat_name,cat_doc in std_cat_dict.items():
		query_dist.append(np.dot(query_vec,cat_doc))
		distance=np.dot(query_vec,cat_doc)

		try:
			sim=encoder.model.similarity(query_vec,cat_doc)
			print("%s similarity: %0.5f"%(cat_name,sim))
		except:
			continue

	if disp:
		for cat_name, cat_doc in std_cat_dict.items():
			distance = np.dot(query_vec, cat_doc)
			print("%s: %0.2f" % (cat_name, distance))
	return np.array(query_dist)

def std_categories_to_vectors(query, encoder, fname="std_categories.tsv"):

	cat_dict={}
	with open(fname,"r") as f:
		for line in f:
			items=line.strip().split("\t")
			name=items[0]
			docvec=encoder.model.infer_vector(items[1:])
			#print(docvec)
			cat_dict[name]=docvec 
			print("name:%s\t%d"%(name,docvec.size))

	labels
	for cat_name, cat_doc in cat_dict.items():
		distance = np.dot(query.model.infer_vector(query), cat_doc)
		print("%s: %0.2f" % (cat_name, distance))

def get_most_recent_doc2vec(directory="WikiLearn/data/models/doc2vec"):
	items=os.listdir(directory)
	newest=None 
	for item in items:
		try:
			timestamp=int(item.split("-")[0].split(":")[1])
			if timestamp>newest:
				newest=timestamp
				newest_name=os.path.join(directory,item)
		except:
			continue
	print(newest_name)
	return newest_name

def main():
	start_time = time.time()


	# interactive converter from article id to title
	convert_ids_to_titles=False  
	if convert_ids_to_titles:
		f=open("titles.tsv","r")
		title_dict={}
		i=0
		for line in f:
			i+=1
			sys.stdout.write("\rMapping titles %d"%i)
			items=line.strip().split("\t")
			if len(items)==2:
				title_dict[items[0]]=items[1]
		f.close()
		sys.stdout.write("\n")
		while True:
			t = raw_input("Enter id: ")
			if t=="q": break 
			try:
				title = title_dict[t]
				print(title)
			except:
				print("Could not find title")
		return

	# create "source qualities" for each article
	create_source_qualities=False  
	if create_source_qualities:

		f=open("quality.tsv","r")
		qual_dict={}
		i=0
		for line in f:
			i+=1
			sys.stdout.write("\rCreating qualities dict %d"%i)
			items=line.strip().split("\t")
			if len(items)==2:
				qual_dict[items[0]]=items[1]
		f.close()
		sys.stdout.write("\n")

		f=open("links.tsv","r")
		link_dict={}
		i=0
		total_links=0
		for line in f:
			i+=1
			sys.stdout.write("\rCreating links dict %d | Avg. Num: %0.3f"%(i,float(total_links/i)))
			items=line.strip().split("\t")
			if len(items)==2:
				link_dict[items[0]]=items[1].split(" ")
				total_links += len(items[1].split(" "))
			else:
				i+=-1
		f.close()
		sys.stdout.write("\n")

		link_mapping = {"fa":6,"a":5,"ga":4,"b":3,"c":2,"start":1,"stub":0}
		link_mapping_rev = {7:"fa",6:"fa",5:"a",4:"ga",3:"b",2:"c",1:"start",0:"stub"}

		f_dest=open("link_quality-ids.tsv","w")
		j=0
		dropped=0
		for article_id,link_ids in link_dict.items():
			j+=1
			sys.stdout.write("\rCreating link qualities (%d/%d) | Dropped: %d"%(j,i,dropped))
			if len(link_ids)<1:
				dropped+=1
				continue
			try:
				num_links=0
				link_qualities=0
				for l in link_ids:
					try:
						link_qual = qual_dict[l]
						link_qualities+=link_mapping[link_qual]
						num_links+=1
					except: 
						continue

				avg_qual = int(float(link_qualities)/float(num_links)+0.5)
				avg_qual_label = link_mapping_rev[avg_qual]
				f_dest.write("%s\t%s\n"%(article_id,avg_qual_label))

			except:
				dropped+=1
		f_dest.close()
		sys.stdout.write("\n")
		return

	push_source_qualities=True 
	if push_source_qualities:

		import psycopg2
		from psycopg2 import connect
		from bisect import bisect_left

		# connecting to database
		username = "waynesun95"
		host = "aa9qiuq51j8l7b.cja4xyhmyefl.us-east-1.rds.amazonaws.com"
		port = "5432"
		dbname = "ebdb"
		password = raw_input("Enter server password: ")

		sys.stdout.write("Trying to connect... ")
		try:
			server_conn = connect("user="+username+" host="+host+" port="+port+" password="+password+" dbname="+dbname)
		except:
			sys.stdout.write("failure\n")
			return
		sys.stdout.write("success\n")

		command_str = "UPDATE articles as t set"
		command_str += " source_quality = c.source_quality "
		command_str += "from (values"

		num_total = len(open("link_quality-ids.tsv","r").split("\n"))
		i=0
		dropped=0
		sent=0
		f=open("link_quality-ids.tsv","r")
		for line in f:
			i+=1 
			sys.stdout.write("\rPreparing server data %d | Dropped:%d | Sent:%d"%(i,dropped,sent))

			items=line.strip().split("\t")
			if len(items)==2:
				a_id = items[0]
				qual_str = items[1]

				command = " (\'"+qual_str+"\', "+str(a_id)+")"
				command_str+=command 

				if i%5000==0 or i==num_total:
					command_str += " ) as c(source_quality, title) where c.id = t.id;"
					cursor=server_conn.cursor()
					cursor.execute(command_str)
					server_conn.commit()
					sent+=1 

					command_str = "UPDATE articles as t set"
					command_str += " source_quality = c.source_quality "
					command_str += "from (values"
				else:
					command_str += ","
		f.close()
		sys.stdout.write("\n")


	create_deeper_categories=False 
	if create_deeper_categories:

		cat_parents_dict={}
		total_len=1.0
		f=open("category_parents-string.tsv","r")
		i=0
		for line in f:
			i+=1
			sys.stdout.write("\rMapping category parents (%d) | Avg. len: %0.5f"%(i,float(total_len/i)))
			items=line.strip().split("\t")
			if len(items)>1:
				cat_parents_dict[items[0]]=items[1:]
				total_len+=len(items[1:])
			else:
				i-=1

		f.close()
		sys.stdout.write("\n")
		dropped=0
		i=0
		total_len=1.0
		limit_depth_to=2 # two steps up tree max
		for c in cat_parents_dict.keys():
			i+=1
			expand_at=0
			orig_len=len(cat_parents_dict[c])
			break_len=-1
			while True:
				if expand_at==orig_len: break_len=len(cat_parents_dict[c])
				if expand_at==break_len and limit_depth_to==2: break 
				if expand_at>=len(cat_parents_dict[c]): break 
				sys.stdout.write("\rDeepening categories %d | Avg. len:%0.5f"%(i,float(total_len/i)))
				old_categories=cat_parents_dict[c]
				expanding_parent = old_categories[expand_at]
				try: new_parents = cat_parents_dict[expanding_parent]
				except: new_parents=[]
				if len(new_parents)!=0: 
					for n in new_parents:
						if n not in cat_parents_dict[c]: cat_parents_dict[c].append(n)
				expand_at+=1
			total_len+=len(cat_parents_dict[c])
		sys.stdout.write("\n")

		f_dest=open("categories_deeper-string.tsv","w")
		f=open("categories-string.tsv","r")
		total_len=0
		i=0
		dropped=0
		for line in f:
			i+=1
			sys.stdout.write("\rExpanding categories (%d) | Avg. len: %0.5f | Dropped:%d"%(i,float(total_len/i),dropped))
			items=line.split("\t")
			if len(items)<2: continue
			article_title,current_categories = line.strip().split("\t")
			initial_categories=current_categories.split(" ")
			f_dest.write("%s\t"%(article_title))
			f_dest.flush()
			for c in initial_categories:
				f_dest.write("%s "%c)
				total_len+=1
				try:
					for c1 in cat_parents_dict[c]:
						f_dest.write("%s "%c1)
						total_len+=1
				except:
					dropped+=1
			f_dest.write("\n")
		f.close()
		f_dest.close()
		sys.stdout.write("\n")
		return

	test_iterator=False  
	if test_iterator:
		corpi=["categories-string.tsv","category_children-string.tsv","titles.tsv"]
		for c in corpi:
			print("\n%s"%c)
			corpus=item_corpus(c,n_examples=100)
			for i in corpus:
				print(i)
		return


	test_doc2vec=False
	if test_doc2vec:

		fname=get_most_recent_doc2vec()
		#fname="WikiLearn/data/models/doc2vec/unix:1493414378-examples:-1-features:300-window:40-epochs:20-ppe:1/"

		encoder=doc2vec()
		encoder.load(fname,spec="backup")
		#std_category_dist("Category:Arts",encoder,True)

		interactive=True 
		if interactive:
			while True:
				article = raw_input("Enter title: ")
				if article=="q": return 
				article=article.replace(" ","_")
				std_category_dist(article,encoder,True)
		else:
			std_category_dist("Anarchism",encoder,True)
		return

	# command line argument to open the gui window
	if len(sys.argv)==2 and sys.argv[1] in ["-g","-gui"]:
		from interface import start_gui
		start_gui()
		return

	require_datadump = False
	if require_datadump:
		if not os.path.isfile('text.tsv'):
			# download (if not already present)
			dump_path = download_wikidump('enwiki','WikiParse/data/corpora/enwiki/data')
			# parse the .xml file
			parse_wikidump(dump_path)

	# if we have a copy of the parsed datadump
	if os.path.isfile('text.tsv'):

		tree=False 
		if tree:
			build_category_tree()
			return

		make_category_strings=False 
		if make_category_strings:

			f=open("titles.tsv","r")
			title_dict={}
			i=0
			for line in f:
				i+=1
				sys.stdout.write("\rBuilding titles dict (%d/34000000)"%(i))
				try:
					article_id,article_title=line.strip().split("\t")
					#sys.stdout.write("\r                                                                                                       ")
					#sys.stdout.write("\rBuilding titles dict (%d) - %s                                                                                  "%(i,article_title))
					title_dict[article_id]=article_title 
				except:
					continue 
			f.close()
			sys.stdout.write("\n")

			cat_dest=open("categories-string.tsv","w")
			cat_src=open("categories.tsv","r")

			i=0
			for line in cat_src:
				try:
					article_id,cat_id = line.strip().split("\t")
					sys.stdout.write("\rSaving (%d)"%i)
					cat_dest.write("%s\t"%(title_dict[article_id]))
					body=' '.join(title_dict[a] for a in cat_id.split(" "))
					cat_dest.write("%s\n"%body)
				except:
					continue
				i+=1
			sys.stdout.write("\n")
			cat_dest.close()
			cat_src.close()
			return


		##############################################################################
		# trains a new Doc2Vec encoder on the contents of text.tsv
		run_doc2vec = False
		if run_doc2vec:

			text=False
			if text:
				# training configuration
				n_examples      = 20000000 # number of articles to consume per epoch 
				features        = 300      # vector length
				context_window  = 8        # words to analyze on either side of current word 
				threads         = 8        # number of worker threads during training
				epochs          = 20       # maximum number of epochs
				pass_per_epoch  = 1        # number of passes across corpus / epoch (gensim default:5)
				print_epoch_acc = True     # print the accuracy after each epoch
				stop_early      = True     # cut off training if accuracy falls 
				backup          = True     # if true, model is saved after each epoch with "-backup" in filename

				model_name  = "unix:%d-examples:%d-features:%d-window:%d-epochs:%d-ppe:%d" % (int(time.time()),n_examples,features,context_window,epochs,pass_per_epoch)
				phraser_dir = 'WikiLearn/data/models/dictionary/text'         # where to save/load phraser from
				model_dir   = "WikiLearn/data/models/doc2vec/%s" % model_name # where to save new doc2vec model

				# print out launch config
				print("\nphraser_dir: %s" % phraser_dir)
				print("model_dir:   %s\n" % (' | '.join(x for x in model_name.split("-"))))

				# create corpus object to allow for text tagging/iteration
				documents = text_corpus('text.tsv', n_examples=n_examples)
				# assemble bigram/trigrams from corpus
				documents.get_phraser(phraser_dir)
				# create doc2vec object    
				encoder = doc2vec()
				# set model hyperparameters
				encoder.build(features=features,context_window=context_window,threads=threads,iterations=pass_per_epoch)
				# train model on text corpus
				encoder.train(corpus=documents,epochs=epochs,directory=model_dir,test=print_epoch_acc,stop_early=stop_early,backup=backup)
			
			category=True 
			if category:
				n_examples = -1
				features = 300
				context_window = 40
				threads=4
				epochs=15
				pass_per_epoch=1
				print_epoch_acc=False
				stop_early=False
				backup=True 

				model_name  = "unix:%d-examples:%d-features:%d-window:%d-epochs:%d-ppe:%d" % (int(time.time()),n_examples,features,context_window,epochs,pass_per_epoch)
				model_dir   = "WikiLearn/data/models/doc2vec/%s" % model_name # where to save new doc2vec model

				print("model_dir:   %s\n" % (' | '.join(x for x in model_name.split("-"))))

				encoder = doc2vec()
				encoder.build(features=features,context_window=context_window,threads=threads,iterations=pass_per_epoch)
				'''
				categories = []
				with open('titles.tsv') as f:
					for line in f:
						doc_id, title = line.split()
						if title.startswith("Category:"):
							print("Title: %s, Doc_id: %s"%(title,doc_id))
							categories.append(TaggedDocument(title,[doc_id]))
				encoder.model.build_vocab(categories)
				'''
				#category_children = item_corpus("category_children-string.tsv", n_examples=-1)
				#encoder.train(corpus=category_children,epochs=10,directory=model_dir,test=print_epoch_acc,stop_early=stop_early,backup=backup)
				#print(encoder.model.wv.vocab)
				documents=item_corpus("categories_deeper-string.tsv", n_examples=-1)
				encoder.train(corpus=documents,epochs=10,directory=model_dir,test=print_epoch_acc,stop_early=stop_early,backup=backup)
				#print(encoder.model.wv.vocab)

		##############################################################################
		test_quality_classifier = False 
		if test_quality_classifier:
			model_dir = "/media/bfaure/Local Disk/Ubuntu_Storage" # holding full model on ssd for faster load
			model_dir = "/home/bfaure/Desktop/WikiClassify2.0 extra/WikiClassify Backup/(2)/doc2vec/older/5"
			classifier_dir = "WikiLearn/data/models/classifier/keras/lstm-classifier_36.h5"

			from keras.models import load_model
			classifier = load_model(classifier_dir)
			encoder = doc2vec()
			encoder.load(model_dir)
			test_classifier(classifier,encoder) 

		train_importance_classifier_docs=False 
		if train_importance_classifier_docs:
			model_dir = "/media/bfaure/Local Disk/Ubuntu_Storage" # holding full model on ssd for faster load
			# very small model for testing
			#model_dir = "/home/bfaure/Desktop/WikiClassify2.0 extra/WikiClassify Backup/(2)/doc2vec/older/5"            
			# directory to save classifier to
			classifier_dir = "WikiLearn/data/models/classifier/importance-docs" 

			encoder = doc2vec()
			encoder.load(model_dir)
			classify_importance_docs(encoder,classifier_dir)

		train_importance_classifier=False
		if train_importance_classifier:
			model_dir = "/media/bfaure/Local Disk/Ubuntu_Storage" # holding full model on ssd for faster load
			# very small model for testing
			#model_dir = "/home/bfaure/Desktop/WikiClassify2.0 extra/WikiClassify Backup/(2)/doc2vec/older/5"            
			# directory to save classifier to
			classifier_dir = "WikiLearn/data/models/classifier/importance" 

			encoder = doc2vec()
			encoder.load(model_dir)
			classify_importance(encoder,classifier_dir)

		train_quality_classifier = False
		if train_quality_classifier:
			#model_dir = get_most_recent_model('WikiLearn/data/models/doc2vec')
			#model_dir = get_most_recent_model('/home/bfaure/Desktop/WikiClassify2.0/WikiLearn/data/models/doc2vec')
			model_dir = "/media/bfaure/Local Disk/Ubuntu_Storage" # holding full model on ssd for faster load
			# very small model for testing
			#model_dir = "/home/bfaure/Desktop/WikiClassify2.0 extra/WikiClassify Backup/(2)/doc2vec/older/5"

			# directory to save classifier to
			classifier_dir = "WikiLearn/data/models/classifier/quality" 
			encoder = doc2vec()
			encoder.load(model_dir)
			classify_quality(encoder,classifier_dir)

		train_us_state_classifier=False 
		if train_us_state_classifier:
			model_dir = "/media/bfaure/Local Disk/Ubuntu_Storage" # holding full model on ssd for faster load
			# very small model for testing
			#model_dir = "/home/bfaure/Desktop/WikiClassify2.0 extra/WikiClassify Backup/(2)/doc2vec/older/5"

			# directory to save classifier to
			classifier_dir = "WikiLearn/data/models/classifier/us_state" 
			encoder = doc2vec()
			encoder.load(model_dir)
			classify_us_state(encoder,classifier_dir)

		train_content_classifier = False  
		if train_content_classifier:
			model_dir = "/media/bfaure/Local Disk/Ubuntu_Storage" # holding full model on ssd for faster load
			model_dir = "WikiLearn/data/models/doc2vec/old"
			# very small model for testing
			#model_dir = "/home/bfaure/Desktop/WikiClassify2.0 extra/WikiClassify Backup/(2)/doc2vec/older/5"

			# directory to save classifier to
			classifier_dir = "WikiLearn/data/models/classifier/content" 
			encoder = doc2vec()
			encoder.load(model_dir)
			classify_content(encoder,classifier_dir)
			
		##############################################################################
		create_content_samples=False 
		if create_content_samples:
			classifier_f =  "WikiLearn/data/models/classifier/content/1493194726/lstm-classifier.h5"
			from keras.models import load_model
			classifier_t = load_model(classifier_f)
			#classifier_t = get_most_recent_classifier("content",spec="best")
			#model_dir = "/media/bfaure/Local Disk/Ubuntu_Storage" # holding full model on ssd for faster load
			model_dir = "WikiLearn/data/models/doc2vec/old"
			#model_dir = "/home/bfaure/Desktop/WikiClassify2.0 extra/WikiClassify Backup/(2)/doc2vec/older/5"

			encoder=doc2vec()
			encoder.load(model_dir)

			class_names,_ = load_standard_categories("std_categories.txt")            
			#print(class_names)

			#class_names=["film","nature","music","athletics","video_game","economics","war","infrastructure_transport","politics","populated_areas","architecture"]
			generate_classifier_samples_words(classifier_t,class_names,encoder,"content-new")

		create_importance_samples=False 
		if create_importance_samples:
			classifier_t = get_most_recent_classifier("importance",spec="last")
			model_dir="/media/bfaure/Local Disk/Ubuntu_Storage" # holding full model on ssd for faster load
			encoder=doc2vec()
			encoder.load(model_dir)

			class_names = ["top","high","mid","low"]
			generate_classifier_samples_words(classifier_t,class_names,encoder,"importance")

		create_quality_samples=False 
		if create_quality_samples:
			classifier_t = get_most_recent_classifier("quality",spec="last")
			model_dir="/media/bfaure/Local Disk/Ubuntu_Storage" # holding full model on ssd for faster load
			encoder=doc2vec()
			encoder.load(model_dir)

			class_names = []
			generate_classifier_samples_words(classifier_t,class_names,encoder,"quality")

		create_us_state_samples=False 
		if create_us_state_samples:
			classifier_t = get_most_recent_classifier("us_state",spec="best")
			model_dir="/media/bfaure/Local Disk/Ubuntu_Storage" # holding full model on ssd for faster load
			encoder=doc2vec()
			encoder.load(model_dir)

			us_states=[]
			s_f=open("us_states.txt","r")
			for line in s_f:
				line = line.strip().lower().replace(" ","_")
				if len(line)>2:
					us_states.append(line)
			s_f.close()
			generate_classifier_samples_words(classifier_t,us_states,encoder,"us_state")

		##############################################################################
		create_us_state_samples_docs=False 
		if create_us_state_samples_docs:
			#classifier_t = get_most_recent_classifier("us_state",spec="epoch_0")
			classifier_t = get_most_recent_classifier("us_state",spec="best")
			model_dir="/media/bfaure/Local Disk/Ubuntu_Storage" # holding full model on ssd for faster load
			#model_dir = "/home/bfaure/Desktop/WikiClassify2.0 extra/WikiClassify Backup/(2)/doc2vec/older/5"
			encoder=doc2vec()
			encoder.load(model_dir)

			us_states=[]
			s_f=open("us_states.txt","r")
			for line in s_f:
				line = line.strip().lower().replace(" ","_")
				if len(line)>2:
					us_states.append(line)
			s_f.close()
			generate_classifier_samples_docs(classifier_t,us_states,encoder,"us_state")
		
		##############################################################################
		# requires categories.tsv & titles.tsv, creates largest_categories.tsv, largest_categories-strings.tsv,
		# largest_categories-meta.txt, article_categories.tsv, sorted_categories.tsv
		# faster after first run (loads sorted_categories.tsv for speed)
		compile_largest_categories=False 
		if compile_largest_categories:
			largest_categories_compiler()
		
		# requires a model and text.tsv, creates similar_articles-string.tsv & similar_articles-ids.tsv
		compile_similar_articles = False 
		if compile_similar_articles:
			print("Compiling similar articles...")
			model_dir = "WikiLearn/data/models/doc2vec/old"
			similar_articles_compiler(model_dir,start_at=884212)

		##############################################################################
		# update the server entries with related articles, requires similar_articled-ids.tsv
		send_similar_articles_to_server = True 
		if send_similar_articles_to_server:
			send_similar_articles(start_at=1010000,fname="similar_articles-ids-new.tsv")

		# update the server entries with quality/importance attributes, requires quality.tsv & importance.tsv
		send_quality_importance_to_server=False
		if send_quality_importance_to_server:
			send_quality_importance(start_at=0)

		##############################################################################
		# DEFUNCT
		# after parser is run, use this to map the article ids (talk ids) in quality.tsv 
		# to the article ids (real article ids) in text.tsv, saved in id_mapping.tsv
		map_talk_to_real = False 
		if map_talk_to_real:
			import Cython
			import subprocess 
			subprocess.Popen('python setup.py build_ext --inplace',shell=True).wait()
			from helpers import map_talk_to_real_ids
			map_talk_to_real_ids("id_mapping.tsv")  

	else:
		print("text.tsv not present, could not create text dictionary")

	print("\nTotal time: %s\n" % make_seconds_pretty(time.time()-start_time))

if __name__ == "__main__":
	main()


