from __future__ import print_function
import json, codecs, time
from datetime import datetime

from operator import attrgetter


class url_t:
    def __init__(self,url):
        self.url = url 
        self.ct = 0

filename = "documents_simple.json"

start_time = time.time()
print("Loading...",end="\r")
with open(filename,"r") as data_file:
    dump = json.load(data_file,"ISO-8859-1")
print("Loading... done, "+str(time.time()-start_time)+" seconds")

urls = []

start_time = time.time()
print("Reading documents...",end="\r")
for article in dump:

    for url in dump[article]['cited_domains']:
        found = False
        for found_url in urls:
            if found_url.url == url:
                found_url.ct = found_url.ct+int(dump[article]['size'])
                found = True
                break
        if found==False:
            new_url = url_t(url)
            new_url.ct = int(dump[article]['size'])
            urls.append(new_url)


print("Reading documents... done, "+str(time.time()-start_time)+" seconds")

sorted_urls = sorted(urls, key=attrgetter('ct'), reverse=True)

for i in range(10):
    print(sorted_urls[i].url+" "+str(sorted_urls[i].ct))



