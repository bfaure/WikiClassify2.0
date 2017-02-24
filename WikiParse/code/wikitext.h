#ifndef WIKITEXT_H
#define WIKITEXT_H

#include <iostream>
using std::cout;

#include <string>
using std::string;
using std::size_t;

#include <vector>
using std::vector;

#include <time.h>
#include <unistd.h>
#include <limits>
#include <stdio.h>
#include <sys/stat.h>
#include <ctype.h>

void decode_text(string &text);
void remove_references(string &text);
void remove_templates(string &text);
void remove_file_references(string &text);
void remove_image_references(string &text);
void remove_html(string &text);

class wikitext {
    private:
        void read_categories(string &text);
        void read_links(string &text);
        void read_citations(string &text);
        void read_text(string &text);
    public:
    	wikitext(string text);
        string text;
        vector<string> categories; 
        vector<string> links;
        vector<string> cited_domains;
        vector<string> cited_authors;
        vector<string> problems;
};

#endif // WIKITEXT_H