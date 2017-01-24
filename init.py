import os

print("Creating directory structure...")

# Creating directories in the /data folder...
for directory in ["WikiParse/data/input", "WikiParse/data/output", "WikiLearn/models"]:
	if not os.path.exists(directory):
		os.makedirs(directory)

print("\tDone!")