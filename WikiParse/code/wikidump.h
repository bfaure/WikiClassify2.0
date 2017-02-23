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
        ofstream debug_file;
    public:
        database();
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