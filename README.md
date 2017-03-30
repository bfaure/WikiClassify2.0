# WikiClassify2.0

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
Run `python main.py` with a `-g` launch parameter to open the user interface main menu.<br>
![Alt text](https://github.com/bfaure/WikiClassify2.0/blob/master/resources/screenshots/main_menu.PNG)

#### [WikiServer]
Enter server credentials.<br>
![Alt text](https://github.com/bfaure/WikiClassify2.0/blob/master/resources/screenshots/login_window.PNG)

View `articles` database.<br>
![Alt text](https://github.com/bfaure/WikiClassify2.0/blob/master/resources/screenshots/table_view.PNG)

Control database actions.<br>
![Alt text](https://github.com/bfaure/WikiClassify2.0/blob/master/resources/screenshots/control_panel.PNG)

#### WikiParse
Configure parser launch parameters.<br>
![Alt text](https://github.com/bfaure/WikiClassify2.0/blob/master/resources/screenshots/parser.PNG)

#### WikiLearn
Live A\* Path Search<br>
![Alt text](https://github.com/bfaure/WikiClassify2.0/blob/master/resources/screenshots/path_connect.png)

## Dependencies
### Python
* `Python 2.7`
* `numpy`   (pip install numpy)
* `g++`     
* `gensim`  (pip install gensim)
* `sklearn` (pip install sklearn))
* `PyQt4`   (apt-get install python-qt4)
* `psycopg2`(pip install psycopg2)

### C++
Both of the following packages can be install via the command line using package manager such as `apt-get` on Ubuntu.
* `libpq-dev`  (apt-get install libpq-dev) 
* `libpqxx-dev`(apt-get install libpqxx-dev)

## Related Repositories

[Chrome Extension](https://github.com/lukewielgus/WikiExtension) 
[Project Website](https://github.com/waynesun95/WikiClassifySite)
[Former Repo](https://github.com/nathankjer/WikiClassify)
