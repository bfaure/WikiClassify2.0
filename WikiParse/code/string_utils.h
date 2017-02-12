#ifndef STRING_UTILS

#include <iostream>
using std::cout;
using std::endl;

#include <fstream>
using std::ifstream;
using std::ofstream;

#include <string>
using std::string;

#include <string.h>

#include <vector>
using std::vector;

#include <algorithm>
using std::find_if;

#include <functional>
using std::not1;
using std::ptr_fun;

#include <locale>
using std::isspace;

string trim(string &s);

unsigned  parse_all(const string &str, const string &tag1, const string &tag2, vector<string> &result);
unsigned   save_all(const string &str, const string &tag1, const string &tag2, void (*f)(string, ofstream&, long long unsigned int&), ofstream &dump_output, long long unsigned int &articles_read, long long unsigned int &articles_saved);
void          parse(const string &str, const string &tag1, const string &tag2, string &result);
unsigned count_text(const string &str, const string &tag);

#define STRING_UTILS
#endif