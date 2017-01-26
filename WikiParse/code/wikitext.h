#ifndef WIKITEXT_H
#define WIKITEXT_H

using namespace std;

#include <string>
#include <vector>
#include <fstream>
#include <time.h>
#include <unistd.h>
#include <limits>
#include <stdio.h>
#include <sys/stat.h>
#include <algorithm>
#include <iostream>
#include <ctype.h>


void remove_target(string &temp, string target);
void remove_target(string &temp, string target);
void remove_references(string &temp);
void remove_between(string &temp, string target, vector<string> endtargets);
void remove_between(string &temp, string target, string endtarget, string code);
void remove_between(string &temp, string target, string endtarget);
void remove_between_r(string &temp, string target, string endtarget);
void remove_nested(string begintarg, string endtarg, string &text, size_t &current, size_t begin, int &openCt, int &ct);
void replace_target(string &temp, string target, string new_target, string code);
void replace_target(string &temp, string target, string new_target);
void replace_target(string &temp, vector<string> target, string new_target);
void replace_target(string &temp, string target, string new_target);
void copy_between(const string &body, const string &target, const vector<string> &endtargets, vector<string> &copies);
void copy_between(const string &body, const string &target, const string &endtarget, vector<string> &copies);


#endif // WIKITEXT_H