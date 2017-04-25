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

def id_to_quality(id):
	f = open("quality.tsv","r")
	lines = f.read().split("\n")
	for l in lines:
		if str(l.split("\t")[0].lower())==(str(id).lower()):
			return l.split("\t")[1]
	return "None"

def main():

	cat_file = "categories.tsv"
	f = open(cat_file,"r")
	categories = {}
	i=0
	for line in f:
		i+=1
		sys.stdout.write("\rReading categories (%d/%d)"%(i,13119700))
		items = line.strip().split("\t")
		if len(items)==2:
			line_cats = items[1].split(" ")
			for l in line_cats:
				try:    
					temp = categories[l]
					categories[l]+=1
				except: 
					categories[l]=0
	sys.stdout.write("\n")
	f.close()
	print("\nFound %d categories"%(len(categories)))

	dest_file = "largest_categories.tsv"

	n_largest = 120
	largest_categories = []
	largest_categories_counts = []
	used = {}

	while len(largest_categories)<n_largest:
		sys.stdout.write("\rCompiling (%d/%d)\n"%(len(largest_categories),n_largest))
		sys.stdout.flush()

		cur_largest = 0
		cur_largest_name = "None"

		for key,val in categories.items():
			if val>cur_largest:
				try:
					temp = used[key]
				except:
					cur_largest = val 
					cur_largest_name = key 

		largest_categories_counts.append(cur_largest)
		largest_categories.append(cur_largest_name)
		used[cur_largest_name] = True
		sys.stdout.write("\rCategory: %s | Article Count: %d\n"%(cur_largest_name,cur_largest))
		sys.stdout.flush()

	print("\nSaving results...")
	f2 = open(dest_file,"w")
	for p,p_ct in zip(largest_categories,largest_categories_counts):
		f2.write("%s\t%d\n"%(p,p_ct))
	f2.close()
	print("Done")

	titles = open("titles.tsv")

	print("\nSaving string results...")
	f3 = open("largest_categories-string.tsv","w")
	for p,p_ct in zip(largest_categories,largest_categories_counts):
		for line in titles:
			try:
				if p==line.split("\t")[0]:
					f3.write("%s\t%d\n"%(line.strip().split("\t")[1],p_ct))
					sys.stdout.write("Category: %s | Count: %d\n"%(line.strip().split("\t")[1],p_ct))
					sys.stdout.flush()
					break
			except:
				continue
	f3.close()

if __name__ == '__main__':
	main()

