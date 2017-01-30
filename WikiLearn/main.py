#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
import os, sys, inspect, time

#                            Local imports
#-----------------------------------------------------------------------------#

if os.name == "nt":
    delim = "\\"
else:
    delim = "/"

email_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+delim+"wikiparse"+delim+"code/email_agent.py"

# change this to your email to get updated when the process is complete
destination_email = "wikiclassify@gmail.com"

print("This process will send an email to "+str(destination_email)+" upon completion with results.")
print("To change the destination address press ctrl+c to escape this and change the \"destination_email\"")
print("field in main.py. Change \"use_email\" to False (main.py) to disable this feature.")

from code.read import corpus
from code.vectorize import doc2vec
from code.vectorize import LDA

#                            Main function
#-----------------------------------------------------------------------------#

def main():
    use_email = True # overrides the can_email bool in the False case
    override_auto_dir_generation = False # override the creation of directory structure
    start_time = time.time()

    if override_auto_dir_generation==False:
        try:
            os.system('cd .. && python init.py')
        except:
            print("WARNING: Could not locate the init.py script.")

    data_dir = '../WikiParse/data/output/'
    
    # change this to the desired source file
    data_file = "documents.txt"
    documents = corpus(data_dir+data_file)
    
    #documents = corpus(data_dir+'documents.txt')
    #for doc in documents:
    #    print(doc)

    if False:
        encoder = LDA(documents, 'models')
        print(encoder.get_topics())
        
        #for doc in encoder:
        #    print(doc)
        use_case = "LDA"
    
    if True:
        encoder  = doc2vec(documents, 'models')
        #encoder.outlier()
        #encoder.analogy()
        use_case = "doc2vec"

    if use_email:
        msg_body = "Execution_time-"+str(time.time()-start_time)+"+"
        msg_body += "Document_path-"+data_dir
        os.system('python '+email_path+" "+destination_email+" "+msg_body+" "+use_case)

if __name__ == "__main__":
    main()