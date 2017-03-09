#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os, sys, time
#                          Search Related imports
#-----------------------------------------------------------------------------#
from time import time
import heapq, codecs
from difflib import SequenceMatcher
#                            Local imports
#-----------------------------------------------------------------------------#
from WikiParse.main           import download_wikidump, parse_wikidump, gensim_corpus
from WikiLearn.code.vectorize import LDA, doc2vec
#                            Main function
#-----------------------------------------------------------------------------#

def save_related():

	encoder_directory = 'WikiLearn/data/models/tokenizer'
	doc_ids = dict([x.strip().split('\t') for x in open('titles.tsv')])

	encoder = get_encoder('text.tsv',True,encoder_directory+'/text',400,10,5,10,10)
	#save_related_tokens(encoder, 'output/related_tokens/words.tsv')
	#save_related_docs(encoder, 'output/related_docs/by_words.tsv')
	#save_doc_strings(doc_ids, 'output/related_docs/by_words.tsv', 'output/related_docs_(readable)/by_words.tsv')

	encoder = get_encoder('categories.tsv',False,encoder_directory+'/categories',200,300,1,5,20)
	#save_related_tokens(encoder, 'output/related_tokens/categories.tsv')
	#save_doc_strings(doc_ids, 'output/related_tokens/categories.tsv', 'output/related_tokens_(readable)/categories.tsv')
	#save_related_docs(encoder, 'output/related_docs/by_categories.tsv')
	#save_doc_strings(doc_ids, 'output/related_docs/by_categories.tsv', 'output/related_docs_(readable)/by_categories.tsv')

	encoder = get_encoder('links.tsv',False,encoder_directory+'/links',400,500,1,5,20)
	#save_related_tokens(encoder, 'output/related_tokens/links.tsv')
	#save_doc_strings(doc_ids, 'output/related_tokens/links.tsv', 'output/related_tokens_(readable)/links.tsv')
	#save_related_docs(encoder, 'output/related_docs/by_links.tsv')
	#save_doc_strings(doc_ids, 'output/related_docs/by_links.tsv', 'output/related_docs_(readable)/by_links.tsv')


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
	documents  = gensim_corpus(tsv_path,directory,make_phrases)
	encoder    = doc2vec(documents, directory)
	if not os.path.isfile(os.path.join(directory,'word2vec.d2v')):
		encoder.build(features, context_window, min_count, negative)
		encoder.train(epochs)
		encoder.save(directory)
	else:
		encoder.load(directory)
	return encoder

class elem_t:
	def __init__(self,value,parent=None,cost=None):
		self.value = value 
		self.parent = parent 
		self.cost = cost
		self.column_offset = 0

class PriorityQueue:
	def __init__(self):
		self._queue = []
		self._index = 0
		#self._contents = {}

	def push(self,item):
		#self._contents[item.value] = True
		heapq.heappush(self._queue, (item.cost,self._index,item) )
		self._index +=1

	def top(self):
		return self._queue[0][-1]

	def pop(self):
		index,item = heapq.heappop(self._queue)[1:]
		#self._contents[item.value] = False
		return item 

	def length(self):
		return len(self._queue)

	def clear(self):
		self._queue = []
		self._index = []

	def has(self,value):
		'''
		if value in self._contents: return True
		else: return False
		'''
		for item in self._queue:
			queued_elem = item[-1]
			if queued_elem.value==value: return True
		return False
		
	def update(self,new_elem):
		i=0
		for cost,_,queued_elem in self._queue:
			if queued_elem.value==new_elem.value:
				del self._queue[i]
				break
			i+=1
		self.push(new_elem)

	def get_cost(self,value):
		for cost,_,item in self._queue:
			if item.value==value: return cost 
		return -1

def get_transition_cost(word1,word2,encoder):
	return 1.0-float(encoder.model.similarity(word1,word2)) 

def rectify_path(path_end,dictionary=None):
	path = []
	offsets = []

	cur = path_end
	path.append(path_end.value)
	offsets.append(path_end.column_offset)

	while True:
		cur = cur.parent
		if cur==None: break
		path.append(cur.value)
		offsets.append(cur.column_offset)

	if dictionary is not None:
		for i in range(len(path)):
			path[i] = dictionary[path[i]]

	return path,offsets 
	

def string_compare(str1,str2):
	return SequenceMatcher(None,str1,str2).ratio()

def astar_convene_3(start_query,middle_query,end_query,encoder,weight=4.0,branching_factor=10.0,dictionary=None):
	if dictionary is not None:
		saved_start_query = start_query 
		saved_end_query = end_query 
		start_key = None 
		end_key = None

		try:
			start_key = next(key for key,value in dictionary.items() if value==start_query)
		except:
			try:
				start_key = next(key for key,value in dictionary.items() if value.lower()==start_query.lower())
			except:
				print("Could not find dictionary id for "+start_query)
				for key,value in dictionary.items():
					#if abs(len(value)-len(saved_start_query))>2: continue
					if value.lower()[:9]!=start_query.lower()[:9]: continue
					if string_compare(value.lower()[9:],start_query.lower()[9:])>=0.7:
						wants_this = raw_input("Did you mean \""+value+"\"? [Y,n,restart]: ")
						if wants_this in ["y","Y","yes","Yes",""]:
							start_key = key 
							saved_start_query = value 
							break
						if wants_this in ["r","restart"]:
							print("Canceling search.")
							return

		if start_key==None: 
			print("Canceling search, could not locate "+start_query)
			return -1

		try:
			end_key = next(key for key,value in dictionary.items() if value==end_query)
		except:
			try:
				end_key = next(key for key,value in dictionary.items() if value.lower()==end_query.lower())
			except:
				print("Could not find dictionary id for "+end_query)
				for key,value in dictionary.items():
					if value.lower()[:9]!=start_query.lower()[:9]: continue
					#if abs(len(value)-len(saved_end_query))>2: continue
					if string_compare(value.lower()[9:],end_query.lower()[9:])>=0.7:
						wants_this = raw_input("Did you mean \""+value+"\"? [Y,n,restart]: ")
						if wants_this in ["y","Y","yes","Yes",""]:
							end_key = key 
							saved_end_query = value 
							break
						if wants_this in ["r","restart"]:
							print("Canceling search.")
							return

		if start_key==None or end_key==None: return -1

		start_query = start_key 
		end_query = end_key

	start_vector = encoder.get_nearest_word(start_query,topn=branching_factor)
	end_vector = encoder.get_nearest_word(end_query,topn=branching_factor)

	if start_vector==None:  print("Could not find relation vector for "+start_query)
	if end_vector==None:    print("Could not find relation vector for "+end_query)
	if start_vector==None or end_vector==None: return -1

	start_elem = elem_t(start_query,parent=None,cost=0)
	
	frontier = PriorityQueue()
	start_elem_cost = get_transition_cost(start_query,end_query,encoder)
	start_elem.cost = start_elem_cost
	frontier.push(start_elem)

	cost_list = {}
	cost_list[start_query] = 0

	path_end = start_elem 
	base_cost = 0
	explored = []
	search_start = time()
	return_code = "NONE"

	middle_word = "NONE"
	dist_middle_start = 1000
	dist_middle_end = 1000
	dist_middle_middle = 1000

	while True:
		print("explored: "+str(len(explored))+", frontier: "+str(frontier.length())+", time: "+str(time()-search_start)[:6]+", cost: "+str(base_cost)[:5],end="\r")
		sys.stdout.flush()

		if frontier.length()==0:
			print("\nA* Convene failed.")
			return_code = "NOT FOUND"
			break

		cur_node = frontier.pop()
		cur_word = cur_node.value
		explored.append(cur_word)

		if cur_word not in [start_query,end_query,middle_query]:
			dist_to_middle = get_transition_cost(cur_word,middle_query,encoder)
			dist_to_start = get_transition_cost(cur_word,start_query,encoder)
			dist_to_end = get_transition_cost(cur_word,end_query,encoder)
			if dist_to_end<dist_middle_start and dist_to_start<dist_middle_end and dist_to_middle<dist_middle_middle:
				middle_word = cur_word 
				dist_middle_start = dist_to_start
				dist_middle_end = dist_to_end
				dist_middle_middle = dist_to_middle

		if cur_word==end_query:
			print("\nFound connection.")
			path_end = cur_node 
			break

		neighbors = encoder.get_nearest_word(cur_word,topn=branching_factor)
		if neighbors==None: continue
		base_cost = cost_list[cur_word]

		for neighbor_word in neighbors:
			if cur_word==neighbor_word: continue
			cost = base_cost + get_transition_cost(cur_word,neighbor_word,encoder)

			new_elem = elem_t(neighbor_word,parent=cur_node,cost=cost)
			new_elem.column_offset = neighbors.index(neighbor_word)

			if (neighbor_word not in cost_list or cost<cost_list[neighbor_word]) and neighbor_word not in explored:
				cost_list[neighbor_word] = cost 
				new_elem.cost = cost + (float(weight)*(get_transition_cost(neighbor_word,end_query,encoder))) + (float(weight))*get_transition_cost(neighbor_word,middle_query,encoder)
				frontier.push(new_elem)

	if middle_word=="None":
		print("Words are too similar to be compared, try lower weight & higher branching factor.")
		return

	print("                                                                \r",end="\r")
	print("\n=========================================")
	print(start_query+" + "+middle_query+" + "+end_query+" = "+middle_word+"\n")
	print(middle_word+" --> "+start_query+" similarity = "+str(1-dist_middle_start)[:3])
	print(middle_word+" --> "+middle_query+" similarity = "+str(1-dist_middle_middle)[:3])
	print(middle_word+" --> "+end_query+" similarity = "+str(1-dist_middle_end)[:3])
	print("=========================================")

def astar_convene(start_query,end_query,encoder,weight=4.0,branching_factor=10,dictionary=None):
	if dictionary is not None:
		saved_start_query = start_query 
		saved_end_query = end_query 
		start_key = None 
		end_key = None

		try:
			start_key = next(key for key,value in dictionary.items() if value==start_query)
		except:
			try:
				start_key = next(key for key,value in dictionary.items() if value.lower()==start_query.lower())
			except:
				print("Could not find dictionary id for "+start_query)
				for key,value in dictionary.items():
					#if abs(len(value)-len(saved_start_query))>2: continue
					if value.lower()[:9]!=start_query.lower()[:9]: continue
					if string_compare(value.lower()[9:],start_query.lower()[9:])>=0.7:
						wants_this = raw_input("Did you mean \""+value+"\"? [Y,n,restart]: ")
						if wants_this in ["y","Y","yes","Yes",""]:
							start_key = key 
							saved_start_query = value 
							break
						if wants_this in ["r","restart"]:
							print("Canceling search.")
							return

		if start_key==None: 
			print("Canceling search, could not locate "+start_query)
			return -1

		try:
			end_key = next(key for key,value in dictionary.items() if value==end_query)
		except:
			try:
				end_key = next(key for key,value in dictionary.items() if value.lower()==end_query.lower())
			except:
				print("Could not find dictionary id for "+end_query)
				for key,value in dictionary.items():
					if value.lower()[:9]!=start_query.lower()[:9]: continue
					#if abs(len(value)-len(saved_end_query))>2: continue
					if string_compare(value.lower()[9:],end_query.lower()[9:])>=0.7:
						wants_this = raw_input("Did you mean \""+value+"\"? [Y,n,restart]: ")
						if wants_this in ["y","Y","yes","Yes",""]:
							end_key = key 
							saved_end_query = value 
							break
						if wants_this in ["r","restart"]:
							print("Canceling search.")
							return

		if start_key==None or end_key==None: return -1

		start_query = start_key 
		end_query = end_key

	start_vector = encoder.get_nearest_word(start_query,topn=branching_factor)
	end_vector = encoder.get_nearest_word(end_query,topn=branching_factor)

	if start_vector==None:  print("Could not find relation vector for "+start_query)
	if end_vector==None:    print("Could not find relation vector for "+end_query)
	if start_vector==None or end_vector==None: return -1

	start_similarity = encoder.model.similarity(start_query,end_query)
	print("\nQuery meaning similarity: "+str(start_similarity)[:6])

	start_elem = elem_t(start_query,parent=None,cost=0)
	
	frontier = PriorityQueue()
	start_elem_cost = get_transition_cost(start_query,end_query,encoder)
	start_elem.cost = start_elem_cost
	frontier.push(start_elem)

	cost_list = {}
	cost_list[start_query] = 0

	path_end = start_elem 
	base_cost = 0
	explored = []
	search_start = time()
	return_code = "NONE"

	middle_word = "NONE"
	dist_middle_start = 1000
	dist_middle_end = 1000

	while True:
		print("explored: "+str(len(explored))+", frontier: "+str(frontier.length())+", time: "+str(time()-search_start)[:6]+", cost: "+str(base_cost)[:5],end="\r")
		sys.stdout.flush()

		if frontier.length()==0:
			print("\nA* Convene failed.")
			return_code = "NOT FOUND"
			break

		cur_node = frontier.pop()
		cur_word = cur_node.value
		explored.append(cur_word)

		if cur_word not in [start_query,end_query]:
			dist_to_start = get_transition_cost(cur_word,start_query,encoder)
			dist_to_end = get_transition_cost(cur_word,end_query,encoder)
			if dist_to_end<dist_middle_start and dist_to_start<dist_middle_end:
				middle_word = cur_word 
				dist_middle_start = dist_to_start
				dist_middle_end = dist_to_end

		if cur_word==end_query:
			print("\nFound connection.")
			path_end = cur_node 
			break

		neighbors = encoder.get_nearest_word(cur_word,topn=branching_factor)
		if neighbors==None: continue
		base_cost = cost_list[cur_word]

		for neighbor_word in neighbors:
			if cur_word==neighbor_word: continue
			cost = base_cost + get_transition_cost(cur_word,neighbor_word,encoder)

			new_elem = elem_t(neighbor_word,parent=cur_node,cost=cost)
			new_elem.column_offset = neighbors.index(neighbor_word)

			if (neighbor_word not in cost_list or cost<cost_list[neighbor_word]) and neighbor_word not in explored:
				cost_list[neighbor_word] = cost 
				new_elem.cost = cost + (float(weight)*(get_transition_cost(neighbor_word,end_query,encoder)))
				frontier.push(new_elem)

	if middle_word=="None":
		print("Words are too similar to be compared, try lower weight & higher branching factor.")
		return

	print("                                                                \r",end="\r")
	print("\n=========================================")
	print(start_query+" + "+end_query+" = "+middle_word+"\n")
	print(middle_word+" --> "+start_query+" similarity = "+str(1-dist_middle_start)[:3])
	print(middle_word+" --> "+end_query+" similarity = "+str(1-dist_middle_end)[:3])
	print("=========================================")

def astar_path(start_query,end_query,encoder,weight=4.0,branching_factor=10,dictionary=None):
	
	if dictionary is not None:
		saved_start_query = start_query 
		saved_end_query = end_query 
		start_key = None 
		end_key = None

		try:
			start_key = next(key for key,value in dictionary.items() if value==start_query)
		except:
			try:
				start_key = next(key for key,value in dictionary.items() if value.lower()==start_query.lower())
			except:
				print("Could not find dictionary id for "+start_query)
				for key,value in dictionary.items():
					#if abs(len(value)-len(saved_start_query))>2: continue
					if value.lower()[:9]!=start_query.lower()[:9]: continue
					if string_compare(value.lower()[9:],start_query.lower()[9:])>=0.7:
						wants_this = raw_input("Did you mean \""+value+"\"? [Y,n,restart]: ")
						if wants_this in ["y","Y","yes","Yes",""]:
							start_key = key 
							saved_start_query = value 
							break
						if wants_this in ["r","restart"]:
							print("Canceling search.")
							return

		if start_key==None: 
			print("Canceling search, could not locate "+start_query)
			return -1

		try:
			end_key = next(key for key,value in dictionary.items() if value==end_query)
		except:
			try:
				end_key = next(key for key,value in dictionary.items() if value.lower()==end_query.lower())
			except:
				print("Could not find dictionary id for "+end_query)
				for key,value in dictionary.items():
					if value.lower()[:9]!=start_query.lower()[:9]: continue
					#if abs(len(value)-len(saved_end_query))>2: continue
					if string_compare(value.lower()[9:],end_query.lower()[9:])>=0.7:
						wants_this = raw_input("Did you mean \""+value+"\"? [Y,n,restart]: ")
						if wants_this in ["y","Y","yes","Yes",""]:
							end_key = key 
							saved_end_query = value 
							break
						if wants_this in ["r","restart"]:
							print("Canceling search.")
							return

		if start_key==None or end_key==None: return -1

		start_query = start_key 
		end_query = end_key

	start_vector = encoder.get_nearest_word(start_query,topn=branching_factor)
	end_vector = encoder.get_nearest_word(end_query,topn=branching_factor)

	if start_vector==None:  print("Could not find relation vector for "+start_query)
	if end_vector==None:    print("Could not find relation vector for "+end_query)
	if start_vector==None or end_vector==None: return -1

	start_similarity = encoder.model.similarity(start_query,end_query)
	print("\nQuery meaning similarity: "+str(start_similarity)[:6])

	start_elem = elem_t(start_query,parent=None,cost=0)
	
	frontier = PriorityQueue()
	start_elem_cost = get_transition_cost(start_query,end_query,encoder)
	start_elem.cost = start_elem_cost
	frontier.push(start_elem)

	cost_list = {}
	cost_list[start_query] = 0

	path_end = start_elem 
	base_cost = 0
	explored = []
	search_start = time()
	return_code = "NONE"

	while True:
		print("explored: "+str(len(explored))+", frontier: "+str(frontier.length())+", time: "+str(time()-search_start)[:6]+", cost: "+str(base_cost)[:5],end="\r")
		sys.stdout.flush()

		if frontier.length()==0:
			print("\nA* Search failed to find a connecting path.")
			return_code = "NOT FOUND"
			break

		cur_node = frontier.pop()
		cur_word = cur_node.value
		explored.append(cur_word)

		if cur_word==end_query:
			print("\nFound connection.")
			path_end = cur_node 
			break

		neighbors = encoder.get_nearest_word(cur_word,topn=branching_factor)
		if neighbors==None: continue
		base_cost = cost_list[cur_word]

		for neighbor_word in neighbors:
			if cur_word==neighbor_word: continue
			cost = base_cost + get_transition_cost(cur_word,neighbor_word,encoder)

			new_elem = elem_t(neighbor_word,parent=cur_node,cost=cost)
			new_elem.column_offset = neighbors.index(neighbor_word)

			if (neighbor_word not in cost_list or cost<cost_list[neighbor_word]) and neighbor_word not in explored:
				cost_list[neighbor_word] = cost 
				new_elem.cost = cost + (float(weight)*(get_transition_cost(neighbor_word,end_query,encoder)))
				frontier.push(new_elem)

	print("                                                                \r",end="\r")
	print("\n=========================================")
	print("Reconstructing path...\n")
	solution_path,offsets = rectify_path(path_end,dictionary)
	for item,offset in zip(reversed(solution_path),reversed(offsets)):
		#indent = ''.join("=" for _ in range(offset))
		#if len(indent)==0: indent = ""
		#print(indent+item)
		if solution_path.index(item) in [0,len(solution_path)-1]:
			print("\""+item+"\"")
		else:
			print("-->\t\""+item+"\"  ("+str(offset)+") \t")
	print("=========================================")

def ucs_algo(start_query,end_query,encoder,dictionary=None):
	start_vector = encoder.get_nearest_word(start_query)
	end_vector = encoder.get_nearest_word(end_query)

	if start_vector==None: print("Could not find relation vector for "+start_query)
	if end_vector==None: print("Could not find relation vector for "+end_query)
	if start_vector==None or end_vector==None: return -1

	start_elem = elem_t(start_query,parent=None,cost=0)
	
	frontier = PriorityQueue()
	frontier.push(start_elem)

	path_end = start_elem 
	path_cost = 0
	explored = []
	search_start = time()
	return_code = "NONE"

	while True:

		print("explored: "+str(len(explored))+", frontier: "+str(frontier.length())+", time: "+str(time()-search_start)[:6]+", cost: "+str(path_cost)[:5],end="\r")
		sys.stdout.flush()

		if frontier.length()==0:
			print("\nUniform-Cost Search failed to find a connecting path.")
			return_code = "NOT FOUND"
			break

		cur_node = frontier.pop()
		path_cost = cur_node.cost 

		if cur_node.value == end_query:
			print("\nFound connection.")
			path_end = cur_node
			break

		explored.append(cur_node.value)
		neighbors = encoder.get_nearest_word(cur_node.value)
		if neighbors==None: continue
		
		base_cost = path_cost

		for neighbor in neighbors:
			if neighbor==cur_node.value: continue
			#transition_cost = encoder.model.similarity()
			cost = base_cost+get_transition_cost(cur_node.value,neighbor,encoder)
			#base_cost+=0.1
			new_elem = elem_t(neighbor,parent=cur_node,cost=cost)
			new_elem.column_offset = neighbors.index(neighbor)

			if neighbor not in explored and not frontier.has(neighbor): frontier.push(new_elem)
			elif frontier.has(neighbor) and frontier.get_cost(neighbor)>base_cost:  frontier.update(new_elem)

	print("                                                                \r",end="\r")
	print("\n=========================================")
	print("Reconstructing path...\n")
	solution_path,offsets = rectify_path(path_end)
	for item,offset in zip(reversed(solution_path),reversed(offsets)):
		indent = ''.join("=" for _ in range(offset))
		if len(indent)==0: indent = ""
		print(indent+item)
	print("=========================================")

def get_shortest_path(start_query,end_query,encoder,algo="UCS",dictionary=None,middle_query=None):
	default_b_factor = 15
	default_weight = 4
	sys.stdout.write("\nCalculating shortest vector from \""+str(start_query)+"\" to \""+str(end_query)+"\"...")

	if algo == "UCS":
		sys.stdout.write(" using UCS\n\n")
		return ucs_algo(start_query,end_query,encoder,dictionary=dictionary)
	elif algo in ["A*","C*","3C*"]:  
		sys.stdout.write(" using "+algo+"\n\n")
		print("Note: high branching factor 	- less depth in final path")
		print("Note: high A* weight 		- low cost but slower")
		while True:
			b_factor = raw_input("Enter branching factor (5-100) ["+str(default_b_factor)+"]: ")
			if b_factor == "":
				b_factor = default_b_factor

			if b_factor in ["exit","Exit"]:
				return
			try:
				b_factor = int(b_factor)
				break
			except: continue
		while True:
			weight = raw_input("Enter A* weight (1-100) ["+str(default_weight)+"]: ")
			if weight=="":
				weight = default_weight

			if weight in ["exit","Exit"]:
				return
			try:
				weight = float(weight)
				break
			except: continue
		print("\n")
		if algo=="3C*": return astar_convene_3(start_query,middle_query,end_query,encoder,weight,b_factor)
		if algo=="A*": return astar_path(start_query,end_query,encoder,weight=weight,branching_factor=b_factor,dictionary=dictionary)
		if algo=="C*": return astar_convene(start_query,end_query,encoder,weight=weight,branching_factor=b_factor,dictionary=dictionary)
	else: print("ERROR: algo input not recognized")

def prep_3cstar(encoder):
	while True:
		query1 = raw_input("\nFirst query: ")
		if query1 in ["exit","Exit"]: break
		query2 = raw_input("Second query: ")
		if query2 in ["exit","Exit"]: break
		query3 = raw_input("Third query: ")
		if query3 in ["exit","Exit"]: break
		if query1==" " or query2==" " or query3==" ": continue
		query1 = query1.replace(" ","_")
		query1 = query1.lower()
		query2 = query2.replace(" ","_")
		query2 = query2.lower()
		query3 = query3.replace(" ","_")
		query3 = query3.lower()
		dictionary = None 
		get_shortest_path(query1,query2,encoder,algo="3C*",middle_query=query3)
		print("\n")

def path_search_interface():

	encoder_directory = "WikiLearn/data/models/tokenizer"
	
	doc_ids = dict([x.strip().split('\t') for x in open('titles.tsv')])

	print("Loading encoders...")
	text_encoder = get_encoder('text.tsv',True,encoder_directory+"/text",300,10,5,20,10)
	cat_encoder = get_encoder('categories.tsv',False,encoder_directory+'/categories',200,300,1,5,20)
	link_encoder = get_encoder('links.tsv',False,encoder_directory+'/links',400,500,1,5,20)

	while True:
		algo = raw_input("\nWhich algorithm (UCS, [A*], C*, or 3C*): ")
		if algo in ["ucs","UCS"]: 
			algo = "UCS"
			break
		if algo in ["a*","A*","astar","AStar","a_star","A_star",""]:
			algo = "A*"
			break
		if algo in ["convene","c","c*","C*"]:
			algo = "C*"
			break
		if algo in ["3c","3C","3C*","3c*","3"]:
			return prep_3cstar(text_encoder)

		if algo in ["exit","Exit"]:
			return

	while True:
		query1 = raw_input("\nFirst query: ")
		if query1 in ["exit","Exit"]: break
		query2 = raw_input("Second query: ")
		if query2 in ["exit","Exit"]: break
		if query1==" " or query2==" ": continue
		query1 = query1.replace(" ","_")
		#query1 = query1.lower()
		query2 = query2.replace(" ","_")
		#query2 = query2.lower()

		if algo != "C*":
			while True:
				source = raw_input("\n[\"text\"], \"cat\", or \"link\" based? ")
				if source in ["text","TEXT","Text","t",""]:
					query1 = query1.lower()
					query2 = query2.lower()
					source = text_encoder
					dictionary = None
					break
				if source in ["cat","CAT","Cat","c"]:
					source = cat_encoder 
					query1 = "Category:"+query1
					query2 = "Category:"+query2
					dictionary = doc_ids
					break
				if source in ["link","LINK","Link","l"]:
					print("Link-based WIP")
					continue
					#source = link_encoder
					#dictionary = doc_ids
					#break
				if source in ["exit","Exit"]:
					return
		else:
			query1 = query1.lower()
			query2 = query2.lower()
			dictionary = None 
			source = text_encoder

		get_shortest_path(query1,query2,source,algo=algo,dictionary=dictionary)
		print("\n")
	print("Done")




def main():
	path_interactive = True
	if path_interactive:
		path_search_interface()
		return

	if not os.path.isfile('text.tsv'):
		dump_path = download_wikidump('simplewiki','WikiParse/data/corpora/simplewiki/data')
		parse_wikidump(dump_path)
	if os.path.isfile('text.tsv'):
		save_related()

if __name__ == "__main__":
	main()
