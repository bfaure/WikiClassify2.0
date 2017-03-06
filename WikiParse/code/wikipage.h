#ifndef WIKIPAGE

/* Standard Imports */
#include <iostream>
using std::cout;
using std::ostream;

#include <fstream>
using std::ofstream;

#include <string>
using std::string;
using std::size_t;
using std::stoi;
using std::stol;

#include <vector>
using std::vector;

#include <string.h>
#include <ctype.h>

/* Local Imports */
#include "wikitext.h"
#include "string_utils.h"

void kosher(vector<string> &fields);
void kosher(string &field);

class wikipage {

    private:

        // Get page sections
        void read_title();
        void read_namespace();
        void read_id();
        void read_redirect();
        void read_timestamp();
        void read_text();
        void read_class();
        void read_importance();

        // Make sections safe for saving
        void make_kosher();

    public:
        // Constructor
        wikipage(string page);
        void read();
        void save(ofstream &file);

        // Boolean checks
        bool is_after(unsigned int &year, unsigned int &month, unsigned int &day);
        bool is_article();
        bool is_talk();
        bool is_category();
        bool is_disambig();
        bool is_redirect();

        // Raw page
        string dump_page;

        // Page sections
        unsigned id;
        string title;
        string ns;
        string redirect;

        // Revision sections
        string         year;
        string         month;
        string         day;
        string         text;
        string         importance;
        string         quality;
        vector<string> categories; 
        vector<string> links;
        vector<string> domains;
        vector<string> authors;
        vector<string> problems;
};

#define WIKIPAGE
#endif