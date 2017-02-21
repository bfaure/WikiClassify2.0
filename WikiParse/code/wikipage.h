#ifndef WIKIPAGE

/* Standard Imports */
#include <iostream>
using std::cout;
using std::endl;
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

class wikipage {

    private:
        // Get page sections
        void read_title(string &page);
        void read_namespace(string &page);
        void read_id(string &page);
        void read_revision(string &page);
        void read_redirect(string &page);
        void read_timestamp(string &page);
        void read_contributor(string &page);
        void read_text(string &page);

    public:
        // Constructor
        wikipage(string page);
        void save(ofstream &file);

        // Boolean checks
        bool is_article();
        bool is_talk();
        bool is_category();
        bool is_disambig();
        bool is_redirect();

        // Page sections
        string title;
        string ns;
        unsigned id;
        unsigned long revision;
        string redirect;
        string timestamp;
        string contributor;

        // Text sections
        string text;
        vector<string> categories; 
        vector<string> links;
        vector<string> cited_urls;
        vector<string> cited_authors;
        vector<string> problems;
};

#define WIKIPAGE
#endif