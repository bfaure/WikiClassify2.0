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
#include "string_utils.h"

class wikidump {
    private:
        ifstream dump_input;
        ofstream dump_output;
        ifstream::pos_type dump_size;
        unsigned long long articles_read;
    
    public:
        wikidump(string &path);
        unsigned save_buffer(const string &str);
        void read(string output_directory);
};

#define WIKIDUMP
#endif