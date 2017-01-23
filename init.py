import os

print("Creating directory structure...")

# Creating directories in the /data folder...
curr_dir = "data/"
for directory in ["input", "output"]:
	if not os.path.exists(directory):
		os.makedirs(curr_dir+directory)

print("\tDone!")