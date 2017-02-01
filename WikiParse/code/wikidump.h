#ifndef WIKIDUMP

/* Standard Imports */
#include <iostream>
using std::cout;
using std::endl;
using std::ostream;

#include <fstream>
using std::ifstream;
using std::ofstream;
using std::streampos;
using std::streamoff;

#include <string>
using std::string;
using std::size_t;
using std::getline;
using std::stoi;
using std::remove;
using std::to_string;

#include <string.h>

#include <vector>
using std::vector;

#include <unordered_map>
using std::unordered_map;

#include <set>
using std::set;

#include <vector>
using std::vector;

#include <cstring>

#include <algorithm>
using std::find;
using std::replace;
using std::transform;

#include <ctype.h>

/* Local Imports */
#include "string_utils.h"

class wikidump {

private:
	unsigned long long articles_read;
    ifstream           dump_input;
    ifstream::pos_type dump_size;

public:
    wikidump(string path);
    void read();
    void read(string type);
};

#define WIKIDUMP
#endif