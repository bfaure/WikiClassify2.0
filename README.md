# WikiClassify2.0

# Download Wikipedia
[Link](https://dumps.wikimedia.org/enwiki/latest/). For the entire data dump download `enwiki-lastest-pages-articles.xml`.

## Directory Structure
When first cloning the repo, run the init.py file to create the directory structure expected by the functions (not carried over by git). After this you can place your Wikipedia data dump file (.xml) in the data/sources/ directory. All use case outputs will reside in one of the sub-directories of the data/outputs/ location. Some of the data we have found has been placed at the Google Drive link below.

## Outputs
[Folder here](https://drive.google.com/open?id=0BxJe_Ggl7BIgbGFHd3lkMDA3d3M)

## Instructions
### Parser
`cd` into the WikiClassify2.0/wikiparse directory. Using gcc, from command line enter... <br> `g++ --std=c++11 main.cpp code/wikidump.cpp code/wikitext.cpp code/wikipage.cpp code/string_utils.cpp -o main` <br>... to compile the parser files. To run the program, either enter `./main <path to data dump file>` or modify the main.cpp file such that it includes the path to you're data dump, recompile using the above instruction, and enter simply `./main` to run the program.

### Model

## Dependencies

## Related Repositories

[Chrome Extension](https://github.com/lukewielgus/WikiExtension) <br>
[Project Website](https://github.com/waynesun95/WikiClassifySite) <br>
[Former Repo](https://github.com/nathankjer/WikiClassify)
