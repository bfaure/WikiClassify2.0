# WikiClassify2.0

## Download Wikipedia
[Link](https://dumps.wikimedia.org/enwiki/latest/). For the entire data dump download `enwiki-lastest-pages-articles.xml`.

## Directory Structure
When first cloning the repo, run the init.py file to create the directory structure expected by the functions (not carried over by git). After this you can place your Wikipedia data dump file (.xml) in the data/sources/ directory. All use case outputs will reside in one of the sub-directories of the data/outputs/ location. Some of the data we have found has been placed at the Google Drive link below.

## Outputs
[Folder here](https://drive.google.com/open?id=0BxJe_Ggl7BIgbGFHd3lkMDA3d3M)

## Instructions

### Command Line User Interface
`cd` into the WikiClassify2.0 base directory and run `python main.py` to start the automated workflow in the following order:<br>
* Download latest Wikipedia data dump bz2 archive
* Extract archive into .xml format
* Compile C++ parser files
* Parse .xml data, sending bursts to remove server at 1000 article increments
* Train word2vec and LDA models

After a model is present in the working directory, a subsequent call to `python main.py` will open the interface created to interact with the models (including A\* path search and A\* convene functions). A call to `python main.py` with a `-c` launch parameter will clean the working directory of models and downloaded data.

### Graphic User Interface
Run `python main.py` with a `-g` launch parameter to open the user interface main menu.
![Alt text](https://github.com/bfaure/WikiClassify2.0/blob/master/resources/screenshots/main_menu.PNG)

#### [WikiServer]
Enter server credentials.
![Alt text](https://github.com/bfaure/WikiClassify2.0/blob/master/resources/screenshots/login_window.PNG)

View `articles` database.
![Alt text](https://github.com/bfaure/WikiClassify2.0/blob/master/resources/screenshots/table_view.PNG)

Control database actions.
![Alt text](https://github.com/bfaure/WikiClassify2.0/blob/master/resources/screenshots/control_panel.PNG)

#### WikiParse
#### WikiLearn

## Dependencies
### Python
* `Python 2.7`
* `numpy`
* `g++` (for parser)
* `gensim` (for feature extraction)
* `sklearn` (for classification)
* `PyQt4` (for GUI)
* `psycopg2` (for GUI)
### C++
Both of the following packages can be install via the command line using package manager such as `apt-get` on Ubuntu.
* `libpq-dev`
* `libpqxx-4.0`

## Related Repositories

[Chrome Extension](https://github.com/lukewielgus/WikiExtension) 
[Project Website](https://github.com/waynesun95/WikiClassifySite)
[Former Repo](https://github.com/nathankjer/WikiClassify)

#### Running Parser (temp, debugging C++ files...)
cd into WikiParse/code then compile with...
`g++ --std=c++11 main.cpp wikidump.cpp wikipage.cpp wikitext.cpp string_utils.cpp -o wikiparse.out`
then to run the parser...
`./wikiparse.out <path_to_source> <output_directory>`
for example...
`./wikiparse.out ../data/input/simplewiki-latest-pages-articles.xml ../data/`
