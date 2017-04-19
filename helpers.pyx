import sys
from sets import Set

def get_tsv(tsv_filename):
	f = open(tsv_filename,"r")
	lines = f.read().split("\n")
	items = []
	i=0
	for l in lines:
		i+=1
		sys.stdout.write("\rLoading %s (%d/%d)    " % (tsv_filename,i,len(lines)))
		sys.stdout.flush()
		if len(l.split("\t"))==2: items.append(l.split("\t"))
	f.close()
	sys.stdout.write("\n")
	return items

def get_tsv_column(tsv_filename,col_idx=0):
	print("Loading %s..." % tsv_filename)
	f = open(tsv_filename,"r")
	lines = f.read().split("\n")
	column = []
	for l in lines:
		if len(l.split("\t"))>col_idx: column.append(l.split("\t")[0]) 
	f.close()
	return column

def get_num_articles(cat):
	return len(cat.art_ints)

class category(object):
	def __init__(self,name_str=None,name_int=None,art_int=None):
		self.name_str = name_str  # string rep. of category
		self.name_int = name_int  # integer rep. of category
		self.art_ints = [art_int] # to hold all articles in this category
		self.art_strs = []  	  # to hold all articles in this category

def write_category(cat,device=sys.stdout):
	device.write(str(cat.name_int)+"\t")
	for i in range(len(cat.art_ints)):
		device.write(str(cat.art_ints[i]))
		if i!=(len(cat.art_ints)-1): device.write("\t")
		else: device.write("\n")

def write_categories(cat,device,topn=1000):
	for i in range(1000):
		sys.stdout.write("\rWriting categories (%d/%d)        ",(i,topn) )
		sys.stdout.flush()
		write_category(cat=cat[i],device=device)
	sys.stdout.write("\n")

def map_int_to_str(i_tag,t_map):
	for tag,val in t_map:
		if int(i_tag)==int(tag): return val
	print("\nERROR: no map entry for %s" % str(i_tag))

def map_categories_str(s_cat,t_map,topn=1000):
	i=0
	for s in s_cat:
		i+=1
		sys.stdout.write("\Mapping categories (%d/%d)        ",(i,topn) )
		sys.stdout.flush()
		if s_cat.index(s)==topn: return s_cat
		s.name_str = map_int_to_str(s.name_int,t_map)
		s.art_strs = [(map_int_to_str(e,t_map) for e in s.art_ints)]
	sys.stdout.write("\n")

def write_category_str(cat,device=sys.stdout):
	device.write(str(cat.name_str)+"\t")
	for i in range(len(cat.art_strs)):
		device.write(str(cat.art_strs[i]))
		if i!=(len(cat.art_strs)-1): device.write("\t")
		else: device.write("\n")

def write_categories_str(cat,device,topn=1000):
	for i in range(1000):
		sys.stdout.write("\rWriting string categories (%d/%d)        ",(i,topn) )
		sys.stdout.flush()
		write_category_str(cat=cat[i],device=device)
	sys.stdout.write("\n")

"""
def title_to_id(title):
	f = open("titles.tsv","r")
	lines = f.read().split("\n")
	for l in lines:
		if l.split("\t")[1].lower()==title.lower():
			return l.split("\t")[0]
	return "None"

def id_to_title(id):
	f = open("titles.tsv","r")
	lines = f.read().split("\n")
	for l in lines:
		if str(l.split("\t")[0].lower())==(str(id).lower()):
			return l.split("\t")[1]
	return "None"
"""

def id_to_quality(id):
	f = open("quality.tsv","r")
	lines = f.read().split("\n")
	for l in lines:
		if str(l.split("\t")[0].lower())==(str(id).lower()):
			return l.split("\t")[1]
	return "None"

#######################################################

from bisect import bisect_left

def get_row_id(row):
	return int(row.split("\t")[0])

print("\nReading titles.tsv...")
title_map = open('titles.tsv','r').read().split("\n")
rows = []
for row in title_map:
	items = row.split("\t")
	if len(items)==2: rows.append(row)

print("Sorting rows...")
rows = sorted(rows,key=get_row_id)

print("Splitting rows...")
ids = []
titles = []
for r in rows:
	items = r.split("\t")
	ids.append(int(items[0]))
	titles.append(items[1])

print("Creating dict...")
title_idx_dict = {}
k=-1
for t in titles:
	k+=1
	title_idx_dict[t]=k

def title_to_id(title):
	try:    return str(ids[title_idx_dict[title]])
	except: return None

def binary_search(x,lo=0,hi=None):
	return bisect_left(ids,x,lo,hi or len(ids))

def id_to_title(id):
	return titles[binary_search(id)]

def map_talk_to_real_ids(fname):
	import time 
	start_time = time.time()

	output = open(fname,"w")
	f = open("quality.tsv","r")
	lines = f.read().split("\n")
	i=-1
	for l in lines:
		i+=1
		talk_id = int(l.split("\t")[0])
		real_id = title_to_id(id_to_title(talk_id).replace("Talk:",""))
		if real_id!=None: output.write(str(talk_id)+"\t"+str(real_id))
		if i!=len(lines)-1: output.write("\n")
		sys.stdout.write("\rMapping (%d/%d) %0.2f/sec"%(i,len(lines),float(i/(time.time()-start_time))))
		sys.stdout.flush()
		#if (time.time()-start_time)>10: break

	sys.stdout.write("\n")
	output.close()

def main():
	print("here")
	'''
	cat = get_tsv("categories.tsv")

	sorting = False 
	convert = True

	if sorting:
		categories = []
		categories_seen = []

		i=0
		for a,C in cat:
			i+=1
			sys.stdout.write("\rProcessing categories.tsv (%s/%s)    "%(i,len(cat)))
			sys.stdout.flush()
			cats = C.strip().split(" ")
			for c in cats:
				try:
					categories[categories_seen.index(int(c))].art_ints.append(a)
				except:
					try:
						categories_seen.append(int(c))
						categories.append(category(name_int=int(c),art_int=int(a)))
					except: continue

		sys.stdout.write("\n")

		print("Sorting categories.tsv...")
		sorted_categories = sorted(categories,key=get_num_articles)

		f = open("biggest_categories.tsv","w")
		write_categories(sorted_categories,f)
		f.close()

		title_map = get_tsv("titles.tsv")
		sorted_categories = map_categories_str(s_cat=sorted_categories,t_map=title_map)

		f = open("biggest_categories_str.tsv","w")
		write_categories_str(sorted_categories,f)
		f.close()

	if convert:
		f = open("categories_str.tsv","w")
		title_map = get_tsv("titles.tsv")
		redirects_map = get_redirects

		i=0
		for a,C in cat:
			i+=1 
			sys.stdout.write("\rProcessing categories.tsv (%s/%s)    "%(i,len(cat)))
			sys.stdout.flush()
			cats = C.strip().split(" ")
			if len(cats)>0:
				f.write(map_int_to_str(a,title_map)+"\t")
				for c in cats:
					try:
						f.write(map_int_to_str(int(c,title_map)))
					except: pass 
					if cats.index(c)!=len(cats)-1:
						f.write(" ")
					else:
						f.write("\n")
		sys.stdout.write("\n")
		f.close()
	'''

if __name__ == '__main__':
	main()

