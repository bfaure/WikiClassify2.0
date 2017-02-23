#ifndef STRING_UTILS

#include <iostream>
using std::cout;

#include <fstream>
using std::ofstream;

#include <string>
using std::string;

#include <string.h>

#include <vector>
using std::vector;

#include <algorithm>
using std::find_if;

#include <locale>
using std::isspace;

string trim(string &s);

unsigned    parse_all(const string &str, const string &tag1, const string &tag2, vector<string> &result);
void            parse(const string &str, const string &tag1, const string &tag2, string &result);
unsigned count_string(const string &str, const string &tag);

void remove_between(string &temp, string target, vector<string> endtargets);
void remove_between(string &temp, string target, string endtarget, string code);
void replace_target(string &temp, string target, string new_target, string code);
void remove_nested(string begintarg, string endtarg, string &text, size_t &current, size_t begin, int &openCt, int &ct);
void remove_between(string &temp, string target, string endtarget);
void remove_between_r(string &temp, string target, string endtarget);
void remove_target(string &temp, string target);
void replace_target(string &temp, string target, string new_target);
void replace_target(string &temp, vector<string> target, string new_target);

#define STRING_UTILS
#endif