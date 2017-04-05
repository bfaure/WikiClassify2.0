#ifndef WIKITEXT_H
#define WIKITEXT_H

#include <iostream>
using std::cout;

#include <string>
using std::string;
using std::size_t;

#include <cctype>

#include <vector>
using std::vector;

#include <algorithm>
using std::find;
using std::transform;

#include <time.h>
#include <unistd.h>
#include <limits>
#include <stdio.h>
#include <sys/stat.h>
#include <ctype.h>

class wikitext {
    private:
        void read_quality();
        void read_importance();
        void read_categories();
        void read_links();
        void read_text();
        void read_citations();
        void read_domains(vector<string> &citations);
        void read_authors(vector<string> &citations);
    public:
    	wikitext(string page_text);
        void read_article();
        void read_category();
        void read_talk();

        // Raw text
        string page_text;

        // Parsed text
        string text;
        string importance;
        string quality;
        vector<string> categories; 
        vector<string> links;
        vector<string> domains;
        vector<string> authors;
        vector<string> problems;
};

void parse_domain(string &domain);
void parse_author(string &author);

void decode_text(string &text);
void remove_references(string &text);
void remove_templates(string &text);
void remove_file_references(string &text);
void remove_image_references(string &text);
void remove_html(string &text);

#endif // WIKITEXT_H