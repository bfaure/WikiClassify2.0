#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os, sys, time
from shutil import rmtree

#                          Search Related imports
#-----------------------------------------------------------------------------#
from time import time
import heapq, codecs
from difflib import SequenceMatcher
import numpy as np
import math

#                            Local imports
#-----------------------------------------------------------------------------#
from WikiParse.main           import download_wikidump, parse_wikidump
from WikiLearn.code.vectorize import doc2vec

class elem_t:
    def __init__(self,value,parent=None,cost=None):
        self.value         = value
        self.cost          = cost
        self.column_offset = 0
        self.parent        = parent

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
            if queued_elem.value == value: return True
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
            if item.value == value: return cost
        return -1

def get_transition_cost(word1,word2,encoder):
    return 1.0-float(encoder.model.similarity(word1,word2))

def rectify_path(path_end):
    path    = []
    offsets = []
    cur     = path_end
    path.append(path_end.value)
    offsets.append(path_end.column_offset)
    while True:
        cur = cur.parent
        if cur == None: break
        path.append(cur.value)
        offsets.append(cur.column_offset)
    return path,offsets

def astar_path(start_query,end_query,encoder,branching_factor=60):

    #branching_factor = 75  # Note: high branching factor - less depth in final path
    weight           = 4   # Note: high A* weight - low cost but slower
    
    start_vector = encoder.get_nearest_word(start_query,topn = branching_factor)
    end_vector   = encoder.get_nearest_word(end_query,topn = branching_factor)

    if start_vector == None:                   print("Could not find relation vector for "+start_query)
    if end_vector == None:                     print("Could not find relation vector for "+end_query)
    if start_vector==None or end_vector==None: return []
    
    frontier   = PriorityQueue()
    start_elem = elem_t(start_query,parent=None,cost=get_transition_cost(start_query,end_query,encoder))
    frontier.push(start_elem)
    cost_list              = {}
    cost_list[start_query] = 0
    path_end     = start_elem
    base_cost    = 0
    explored     = []
    search_start = time()
    return_code  = "NONE"
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
        if neighbors == None: continue
        base_cost = cost_list[cur_word]
        for neighbor_word in neighbors:
            if cur_word == neighbor_word: continue
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

def get_queries(encoder, n=None):
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
    queries = [q.lower() for q in queries]
    for q in queries:
        try:
            temp = encoder.model.most_similar(q,topn=1)
        except:
            print('%s not found!' % q)
            return None
    return queries