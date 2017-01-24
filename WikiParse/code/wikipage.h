#ifndef WIKIPAGE

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

class wikipage {

    private:

    	// Page sections
        string title;
        string ns;
        string redirect;
        string timestamp;
        string contributor;
        string comment;
        string text;
        unsigned ID;

        // Get page sections
        void get_title(string &page);
        void get_namespace(string &page);
        void get_redirect(string &page);
        void get_timestamp(string &page);
        void get_contributor(string &page);
        void get_comment(string &page);
        void get_text(string &page);
        void get_ID(string &page);

        // Text sections
        vector<string> categories; 
        vector<string> links;
        unsigned short image_count; 

        // Get text sections
        void read_categories();
        void read_links();
        void read_image_count();

        // Text methods
        void clean_text();
        void percent_decoding();
        void remove_templates();
        void remove_html_elements();
        void remove_file_references();
        void remove_image_references();

    public:

    	// Constructor
        wikipage(string page);
        void save(ofstream &file);

        // Boolean checks
        bool is_redirect();
        bool is_disambig();
        bool is_article();

        bool has_categories();
        bool has_links();

        // Stream I/O
        friend ostream& operator<<(ostream& os, wikipage& wp);
};

#define WIKIPAGE
#endif