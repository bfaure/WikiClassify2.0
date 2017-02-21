#ifndef WIKIDUMP

/* Standard Imports */

#include <iostream>
using std::cout;
using std::endl;
using std::ofstream;

#include <fstream>
using std::ifstream;
using std::ofstream;
using std::streampos;

#include <string>
using std::string;

#include <time.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

/* Local Imports */
#include "wikipage.h"
#include "string_utils.h"

class database {
    private:
        ofstream article_titles;  
        ofstream article_quality;
        ofstream article_importance;
        ofstream article_categories;
        ofstream article_problems;
        ofstream article_revisions;
        ofstream revision_text;
        ofstream category_names;
        ofstream category_parents;
    public:
        database();
        database(string &output_directory);
        void save(wikipage &wp);
};

class wikidump {
    private:
        ifstream dump_input;
        ifstream::pos_type dump_size;
        unsigned long long articles_read;
        database db;
    public:
        wikidump(string &path, string &output_directory);
        unsigned save_buffer(const string &str);
        void read();
};

void kosher(string &field);
void kosher(vector<string> &fields);

#define WIKIDUMP
#endif