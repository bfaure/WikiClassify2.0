import os

def create_directory(directory):
	if not os.path.exists(directory):
		os.makedirs(directory)

print("Creating directory structure...")

# Creating directories in the /data folder...
cur_dir = "data/"
create_directory(cur_dir+"outputs")
create_directory(cur_dir+"sources")

# Creating directories in the /data/outputs folder...
cur_dir = "data/outputs/"
create_directory(cur_dir+"articles")
create_directory(cur_dir+"cats")
create_directory(cur_dir+"simple")
create_directory(cur_dir+"text")

print("Directory structure creation complete.")

