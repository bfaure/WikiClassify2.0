#ifndef WIKIDUMP

/* Standard Imports */

#include <iostream>
using std::cout;
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
        ofstream page_redirects;
        ofstream article_titles;
        ofstream article_revisions;
        ofstream article_revision_timestamp;
        ofstream article_revision_text;
        ofstream article_revision_categories;
        ofstream article_revision_cited_authors;
        ofstream article_revision_cited_domains;
        ofstream article_quality;
        ofstream article_importance;
        ofstream article_problems;
        ofstream category_titles;
        ofstream category_revisions;
        ofstream category_revision_parents;
    public:
        database();
        void open(string &oputput_directory);
        void save_page(wikipage &wp);
        void save_revision(wikipage &wp);
};

class wikidump {
    private:
        ifstream dump_input;
        ifstream::pos_type dump_size;
        database dump_output;
        unsigned long long articles_read;
        unsigned int cutoff_year;
        unsigned int cutoff_month;
        unsigned int cutoff_day;

    public:
        wikidump(string &path, string &output_directory, string &cutoff_date);
        void read();
        unsigned save_buffer(const string &str);
};

#define WIKIDUMP
#endif