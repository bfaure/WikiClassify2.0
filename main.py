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
import numpy as np
import math

#                            Local imports
#-----------------------------------------------------------------------------#
from WikiParse.main           import download_wikidump, parse_wikidump, gensim_corpus
from WikiLearn.code.vectorize import doc2vec

#                            Main function
#-----------------------------------------------------------------------------#

def get_related_tokens(encoder):
    for word in encoder.model.index2word:
        nearest = encoder.get_nearest_word(word)
        print(word+'\t'+'\t'.join(nearest)+'\n')

def get_related_docs(encoder):
    for doc_id in encoder.model.docvecs.offset2doctag:
        nearest = encoder.get_nearest_doc(doc_id)
        print(doc_id+'\t'+'\t'.join(nearest)+'\n')

def get_encoder(tsv_path, make_phrases, directory, features, context_window, min_count, negative, epochs):
    encoder = doc2vec()
    if not os.path.isfile(os.path.join(directory,'word2vec.d2v')):
        encoder.build(features, context_window, min_count, negative)
        documents  = gensim_corpus(tsv_path,directory,make_phrases)
        encoder.train(documents, epochs)
        encoder.save(directory)
    else:
        encoder.load(directory)
    return encoder

class elem_t:
    def __init__(self,value,parent=None,cost=None):
        self.value = value
        self.cost = cost
        self.column_offset = 0
        self.parent = parent

class PriorityQueue:
    def __init__(self):
        self._queue = []
        self._index = 0

    def push(self,item):
        heapq.heappush(self._queue, (item.cost,self._index,item) )
        self._index += 1

    def pop(self):
        index,item = heapq.heappop(self._queue)[1:]
        return item

    def length(self):
        return len(self._queue)

    def has(self,value):
        for item in self._queue:
            queued_elem = item[-1]
            if queued_elem.value == value:
                return True
        return False

    def update(self,new_elem):
        i = 0
        for cost,_,queued_elem in self._queue:
            if queued_elem.value == new_elem.value:
                del self._queue[i]
                break
            i+= 1
        self.push(new_elem)

    def get_cost(self,value):
        for cost,_,item in self._queue:
            if item.value == value:
                return cost
        return -1

def get_transition_cost(word1,word2,encoder):
    return 1.0-float(encoder.model.similarity(word1,word2))

def rectify_path(path_end):
    path = []
    offsets = []
    cur = path_end
    path.append(path_end.value)
    offsets.append(path_end.column_offset)
    while True:
        cur = cur.parent
        if cur == None:
            break
        path.append(cur.value)
        offsets.append(cur.column_offset)
    return path,offsets

def astar_path(start_query,end_query,encoder,branching_factor=60):

    #branching_factor = 75  # Note: high branching factor - less depth in final path
    weight           = 4   # Note: high A* weight - low cost but slower
    
    start_vector = encoder.get_nearest_word(start_query,topn = branching_factor)
    end_vector   = encoder.get_nearest_word(end_query,topn = branching_factor)
    if start_vector == None:
        print("Could not find relation vector for "+start_query)
    if end_vector == None:
        print("Could not find relation vector for "+end_query)
    if start_vector==None or end_vector==None:
        return []
    
    frontier = PriorityQueue()
    start_elem = elem_t(start_query,parent=None,cost=get_transition_cost(start_query,end_query,encoder))
    frontier.push(start_elem)
    cost_list = {}
    cost_list[start_query] = 0
    path_end = start_elem
    base_cost = 0
    explored = []
    search_start = time()
    return_code = "NONE"
    while True:
        if (time()-search_start)>5:
            print('\nTimed out, trying with higher branching factor ('+str(branching_factor+10)+').')
            return astar_path(start_query,end_query,encoder,branching_factor=branching_factor+10)
            return []
        print("explored: "+str(len(explored))+", frontier: "+str(frontier.length())+", time: "+str(time()-search_start)[:6]+", cost: "+str(base_cost)[:5],end='\r')
        sys.stdout.flush()
        if frontier.length() == 0:
            print("\nA* Search failed to find a connecting path.")
            return_code = "NOT FOUND"
            break
        cur_node = frontier.pop()
        cur_word = cur_node.value
        explored.append(cur_word)
        if cur_word == end_query:
            print("\nFound connection.")
            path_end = cur_node
            break
        neighbors = encoder.get_nearest_word(cur_word,topn=branching_factor)
        if neighbors == None:
            continue
        base_cost = cost_list[cur_word]
        for neighbor_word in neighbors:
            if cur_word == neighbor_word:
                continue
            cost = base_cost + get_transition_cost(cur_word,neighbor_word,encoder)
            new_elem = elem_t(neighbor_word,parent=cur_node,cost=cost)
            new_elem.column_offset = neighbors.index(neighbor_word)
            if (neighbor_word not in cost_list or cost<cost_list[neighbor_word]) and neighbor_word not in explored:
                cost_list[neighbor_word] = cost
                new_elem.cost = cost + (float(weight)*(get_transition_cost(neighbor_word,end_query,encoder)))
                frontier.push(new_elem)
    print((' '*64)+'\r',end='\r')
    print('\n'+('='*41))
    print("Reconstructing path...\n")
    solution_path,offsets = rectify_path(path_end)
    return solution_path[::-1]

def ucs_algo(start_query,end_query,encoder):
    start_vector = encoder.get_nearest_word(start_query)
    end_vector = encoder.get_nearest_word(end_query)
    if start_vector == None:
        print("Could not find relation vector for "+start_query)
    if end_vector == None:
        print("Could not find relation vector for "+end_query)
    if start_vector==None or end_vector==None:
        return []
    start_elem = elem_t(start_query,parent=None,cost=0)
    frontier = PriorityQueue()
    frontier.push(start_elem)
    path_end = start_elem
    path_cost = 0
    explored = []
    search_start = time()
    return_code = "NONE"
    while True:
        if (time()-search_start)>5:
            print('Timed out!')
            return []
        print("explored: "+str(len(explored))+", frontier: "+str(frontier.length())+", time: "+str(time()-search_start)[:6]+", cost: "+str(path_cost)[:5],end='\r')
        sys.stdout.flush()
        if frontier.length() == 0:
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
        if neighbors == None:
            continue
        base_cost = path_cost
        for neighbor in neighbors:
            if neighbor == cur_node.value:
                continue
            cost = base_cost+get_transition_cost(cur_node.value,neighbor,encoder)
            new_elem = elem_t(neighbor,parent=cur_node,cost=cost)
            new_elem.column_offset = neighbors.index(neighbor)
            if neighbor not in explored and not frontier.has(neighbor):
                frontier.push(new_elem)
            elif frontier.has(neighbor) and frontier.get_cost(neighbor)>base_cost:
                frontier.update(new_elem)
    print((' '*64)+'\r',end='\r')
    print('\n'+('='*41))
    solution_path,offsets = rectify_path(path_end)
    return solution_path[::-1]

def word_algebra(encoder):
    print("\n")
    print("Deliminate words with \"+\" and \"-\", spaces trimmed (use \"_\"), type \"exit\" to exit...\n")
    while True:
        input_str = raw_input("> ")
        if input_str in ["exit","Exit"]:
            break
        pos = []
        neg = []
        cur_sign = "+"
        cur_buf = None
        for char in input_str:
            if char == " ":
                if cur_buf!=None and cur_sign!=None:
                    if cur_sign == "+":
                        pos.append(cur_buf)
                    if cur_sign == "-":
                        neg.append(cur_buf)
                cur_buf = None
                continue
            if char == "+":
                if cur_buf!=None and cur_sign!=None:
                    if cur_sign == "+":
                        pos.append(cur_buf)
                    if cur_sign == "-":
                        neg.append(cur_buf)
                    cur_buf = None
                cur_sign = "+"
                continue
            if char == "-":
                if cur_buf!=None and cur_sign!=None:
                    if cur_sign == "-":
                        neg.append(cur_buf)
                    if cur_sign == "+":
                        pos.append(cur_buf)
                    cur_buf = None
                cur_sign = "-"
                continue
            if cur_buf is None:
                cur_buf = char
            else:
                cur_buf +=  char
        if cur_buf!=None:
            if cur_sign == "+":
                pos.append(cur_buf)
            if cur_sign == "-":
                neg.append(cur_buf)
        if len(pos)==0 and len(neg)==0:
            print("Didn't catch that...")
            continue
        output = None
        if len(pos)!=0 and len(neg)!=0:
            try:
                output = encoder.model.most_similar_cosmul(positive=pos,negative=neg)
            except KeyError:
                print("One of the words was not in the model (mispelling?)")
                continue
        elif len(pos)!=0:
            try:
                output = encoder.model.most_similar_cosmul(positive=pos)
            except KeyError:
                print("One of the words was not in the model (mispelling?)")
                continue
        elif len(neg)!=0:
            try:
                if len(neg)!=0:
                    output = encoder.model.most_similar(negative=neg)
            except KeyError:
                print("One of the words was not in the model (mispelling?)")
                continue
        if output is not None:
            print(output[0][0])
        else:
            print("Could not calculate result.")

def get_queries(text_encoder, category_encoder, link_encoder, n=None):
    doc_ids = dict([(x.strip().split('\t')[1],x.strip().split('\t')[0]) for x in open('titles.tsv')])
    if n == None:
        queries = []
        query = True
        while query:
            query = raw_input('Query %d: ' % (len(queries)+1))
            if query and query!="":
                queries.append(query)
        print("Using ",queries)
    else:
        queries = [raw_input('Query %d: ' % (q+1)) for q in xrange(n)]
    queries = [q.replace(" ","_") for q in queries]
    while True:
        source = raw_input("\nSelect a type:\nWord [W]\nTitle [t]\nCategory [c]\n> ")
        if source.lower() in ['w','']:
            queries = [q.lower() for q in queries]
            for q in queries:
                try:
                    temp = text_encoder.model.most_similar(q,topn=1)
                except:
                #if q not in text_encoder.model.index2word:
                    print('%s not found!' % q)
                    return None, None
            return queries, text_encoder
        elif source.lower() in ['t']:
            queries = [q[0].upper()+q[1:] for q in queries]
            for i in xrange(len(queries)):
                try:
                    queries[i] = doc_ids[queries[i]]
                except:
                    print('%s not found!' % queries[i])
                    return None, None
            return queries, link_encoder
        elif source.lower() in ['c']:
            queries = ['Category:'+q[0].upper()+q[1:] for q in queries]
            for i in xrange(len(queries)):
                try:
                    queries[i] = doc_ids[queries[i]]
                except:
                    print('%s not found!' % queries[i])
                    return None, None
            return queries, category_encoder

def main():

    doc_ids = dict([x.strip().split('\t') for x in open('titles.tsv')])
    encoder_directory = 'WikiLearn/data/models/tokenizer'
    if not os.path.isfile('titles.tsv'):
        dump_path = download_wikidump('simplewiki','WikiParse/data/corpora/simplewiki/data')
        parse_wikidump(dump_path)
        get_encoder('text.tsv',True,encoder_directory+'/text',400,10,5,10,10)
        get_encoder('categories.tsv',False,encoder_directory+'/categories',200,300,1,5,20)
        get_encoder('links.tsv',False,encoder_directory+'/links',400,500,1,5,20)

    else:
        print("Loading encoders...")
        text_encoder     = get_encoder('text.tsv',True,encoder_directory+"/text",300,10,5,20,10)
        category_encoder = get_encoder('categories.tsv',False,encoder_directory+'/categories',200,300,1,5,20)
        link_encoder     = get_encoder('links.tsv',False,encoder_directory+'/links',200,300,1,5,20)
        while True:
            algo = raw_input("\nSelect an activity:\nPath [P]\nJoin [j]\n> ")#\na: add\n> ")
            if algo.lower() in ["p",""]:
                algo = 'p'
                break
            elif algo.lower() in ["j"]:
                break
        if algo == 'p':
            while True:
                queries, encoder = get_queries(text_encoder, category_encoder, link_encoder, n=2)
                if queries:
                    path = astar_path(queries[0],queries[1],encoder)
                    if all([i.isdigit() for i in path]):
                        for item in path:
                            print(doc_ids[item])
                    else:
                        for item in path:
                            print(item)
                    print('='*41)
        elif algo == 'j':
            while True:
                queries, encoder = get_queries(text_encoder, category_encoder, link_encoder)
                try:
                    middle_word = encoder.model.most_similar(queries,topn=1)[0][0]
                    print((' '*64)+'\r',end='\r')
                    print('\n'+('='*41))
                    #print(" + ".join([doc_ids[q] for q in queries])+" = "+doc_ids[middle_word]+"\n")
                    print(" + ".join(q for q in queries)+" = "+middle_word)
                    print('='*41)
                except:
                    print('One of the words does not occur!')
        #elif algo.lower() in ["add"]:
        #    word_algebra(encoder)

if __name__ == "__main__":
    main()
