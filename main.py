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
#                            Local imports
#-----------------------------------------------------------------------------#

from WikiParse.main           import download_wikidump, parse_wikidump, gensim_corpus
from WikiLearn.code.vectorize import LDA, doc2vec

#                            Main function
#-----------------------------------------------------------------------------#

def save_related():

    encoder_directory = 'WikiLearn/data/models/tokenizer'
    doc_ids = dict([x.strip().split('\t') for x in open('titles.tsv')])

    encoder = get_encoder('text.tsv',True,encoder_directory+'/text',300,10,5,20,10)
    save_related_tokens(encoder, 'output/related_tokens/words.tsv')
    save_related_docs(encoder, 'output/related_docs/by_words.tsv')
    save_doc_strings(doc_ids, 'output/related_docs/by_words.tsv', 'output/related_docs_(readable)/by_words.tsv')

    encoder = get_encoder('categories.tsv',False,encoder_directory+'/categories',200,300,1,5,20)
    save_related_tokens(encoder, 'output/related_tokens/categories.tsv')
    save_doc_strings(doc_ids, 'output/related_tokens/categories.tsv', 'output/related_tokens_(readable)/categories.tsv')
    save_related_docs(encoder, 'output/related_docs/by_categories.tsv')
    save_doc_strings(doc_ids, 'output/related_docs/by_categories.tsv', 'output/related_docs_(readable)/by_categories.tsv')

    encoder = get_encoder('links.tsv',False,encoder_directory+'/links',400,500,1,5,20)
    save_related_tokens(encoder, 'output/related_tokens/links.tsv')
    save_doc_strings(doc_ids, 'output/related_tokens/links.tsv', 'output/related_tokens_(readable)/links.tsv')
    save_related_docs(encoder, 'output/related_docs/by_links.tsv')
    save_doc_strings(doc_ids, 'output/related_docs/by_links.tsv', 'output/related_docs_(readable)/by_links.tsv')


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
    documents = gensim_corpus(tsv_path,directory,make_phrases)
    encoder = doc2vec(documents, directory)
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

    def push(self,item):
        cost = int(item.cost)
        heapq.heappush(self._queue, (cost,self._index,item) )
        self._index +=1

    def top(self):
        return self._queue[0][-1]

    def pop(self):
        index,item = heapq.heappop(self._queue)[1:]
        return item 

    def length(self):
        return len(self._queue)

    def clear(self):
        self._queue = []
        self._index = []
    def has(self,value):
        for item in self._queue:
            queued_elem = item[-1]
            if queued_elem.value==value: return True
        return False

    def update(self,new_elem):
        i=0
        while i<len(self._queue):
            queued_elem = self._queue[i][-1]
            if queued_elem.value==new_elem.value:
                del self._queue[i]
                break
            i+=1
        self.push(new_elem)

    def get_cost(self,value):
        for cost,_,item in self._queue:
            if item.value==value: return cost 
        return -1

def astar_algo(start_query,end_query,encoder,weight=1.0):
    print("Using A* Search...")

    start_vector = encoder.get_nearest_word(start_query)
    end_vector = encoder.get_nearest_word(end_query)

    if start_vector==None: print("Could not find relation vector for "+start_query)
    if end_vector==None: print("Could not find relation vector for "+end_query)
    if start_vector==None or end_vector==None: return -1

    start_elem = elem_t(start_query,parent=None,cost=0)
    
    frontier = PriorityQueue()
    start_elem_cost = float(encoder.model.similarity(start_query,end_query))
    start_elem.cost = start_elem_cost
    frontier.push(start_elem)

    cost_list = {}
    cost_list[start_query] = 0

    path_end = start_elem 
    path_cost = 0
    explored = []
    search_start = time()
    return_code = "NONE"

    f = open("delete_me.txt","w")

    while True:
        print("explored: "+str(len(explored))+", frontier: "+str(frontier.length())+", time: "+str(time()-search_start)[:6]+", cost: "+str(path_cost)[:5],end="\r")
        sys.stdout.flush()

        if frontier.length()==0:
            print("\nA* Search failed to find a connecting path.")
            return_code = "NOT FOUND"
            break

        cur_node = frontier.pop()
        explored.append(cur_node)

        if cur_node.value==end_query:
            print("\nFound connection.")
            path_end = cur_node 
            break

        neighbors = encoder.get_nearest_word(cur_node.value)
        #neighbors = self.by_categories.get_related(cur_node.value)
        if neighbors==None:
            continue
        
        base_cost = cost_list[cur_node.value]+1
        path_cost = base_cost

        for neighbor in neighbors:
            if cur_node.value==neighbor: continue
            #base_cost+= base_cost*0.05

            transition_cost = encoder.model.similarity(cur_node.value,neighbor)
            f.write(str(transition_cost)+"\n")
            cost = base_cost+transition_cost

            new_elem = elem_t(neighbor,parent=cur_node,cost=cost)
            new_elem.column_offset = neighbors.index(neighbor)+1

            if (neighbor not in cost_list or cost<cost_list[neighbor]) and neighbor not in explored:
                cost_list[neighbor] = cost 
                priority = cost + (float(weight) * float((encoder.model.similarity(neighbor,end_query)))/100)
                new_elem.cost = priority 
                frontier.push(new_elem)

    print("                                                                \r",end="\r")
    print("\nReconstructing path...\n")

    def rectify_path(path_end):
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
        return path,offsets 

    solution_path,offsets = rectify_path(path_end)
    for item,offset in zip(reversed(solution_path),reversed(offsets)):
        indent = ''.join("=" for _ in range(offset))
        if len(indent)==0: indent = ""
        print(indent+item)

def ucs_algo(start_query,end_query,encoder):
    print("Using Uniform-Cost Search...")

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
        #neighbors = self.by_categories.get_related(cur_node.value)
        if neighbors==None:
            continue
        
        #neighbors = neighbors[1:]
        base_cost = path_cost

        for neighbor in neighbors:
            #if neighbor==cur_node.value: continue
            base_cost+=0.1

            new_elem = elem_t(neighbor,parent=cur_node,cost=base_cost+encoder.model.similarity(cur_node.value,neighbor))
            new_elem.column_offset = neighbors.index(neighbor)+1

            if neighbor not in explored and not frontier.has(neighbor):
                frontier.push(new_elem)

            elif frontier.has(neighbor) and frontier.get_cost(neighbor)>base_cost: 
                frontier.update(new_elem)

    print("                                                                \r",end="\r")
    print("\nReconstructing path...\n")

    def rectify_path(path_end):
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
        return path,offsets 

    solution_path,offsets = rectify_path(path_end)
    for item,offset in zip(reversed(solution_path),reversed(offsets)):
        indent = ''.join("=" for _ in range(offset))
        if len(indent)==0: indent = ""
        print(indent+item)

def get_shortest_path(start_query,end_query,encoder,algo="UCS"):
    print("\nCalculating shortest vector from "+str(start_query)+" to "+str(end_query)+"...")
    if algo   == "UCS": return ucs_algo(start_query,end_query,encoder)
    elif algo == "A*":  return astar_algo(start_query,end_query,encoder)
    else: print("ERROR: algo input not recognized")

def path_search_interface():

    encoder_directory = "WikiLearn/data/models/tokenizer"
    doc_ids = dict([x.strip().split('\t') for x in open('titles.tsv')])

    print("Loading encoders...")
    text_encoder = get_encoder('text.tsv',True,encoder_directory+"/text",300,10,5,20,10)
    #cat_encoder = get_encoder('categories.tsv',False,encoder_directory+'/categories',200,300,1,5,20)
    #link_encoder = get_encoder('links.tsv',False,encoder_directory+'/links',400,500,1,5,20)

    while True:
        query1 = raw_input("First query: ")
        if query1 in ["exit","Exit"]: break
        query2 = raw_input("Second query: ")
        if query2 in ["exit","Exit"]: break

        query1 = query1.replace(" ","_")
        query1 = query1.lower()
        query2 = query2.replace(" ","_")
        query2 = query2.lower()
        
        if " " in [query1,query2]: continue
        get_shortest_path(query1,query2,text_encoder,algo="A*")
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