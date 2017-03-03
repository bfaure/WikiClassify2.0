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
        void read_revision();
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
        unsigned long  revision;
        string         revision_year;
        string         revision_month;
        string         revision_day;
        string         revision_text;
        string         revision_importance;
        string         revision_quality;
        vector<string> revision_categories; 
        vector<string> revision_links;
        vector<string> revision_cited_domains;
        vector<string> revision_cited_authors;
        vector<string> revision_problems;
};

#define WIKIPAGE
#endif