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

#include <map>
using std::map;

#include <time.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <bzlib.h>

/* Local Imports */
#include "wikipage.h"
#include "string_utils.h"

class database {
    private:

        ofstream titles;
        ofstream redirects;
        ofstream text;
        ofstream categories;
        ofstream links;
        ofstream authors;
        ofstream domains;

        //ofstream quality;
        //ofstream importance;
        //ofstream problems;
        ofstream category_parents;
    public:
        database();
        void save_page(wikipage &wp);
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

        map<string, unsigned> titles;
        map<string, string> redirects;

    public:
        wikidump(string &path, string &cutoff_date);
        void read();
        unsigned save_buffer(const string &str);
};


#define WIKIDUMP
#endif