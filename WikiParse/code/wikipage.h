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

class citation
{
public:
    string citation_type; // book, journal, website, etc. or None if type not recognized
    string author; // FirstName LastName or None if none found
    string url; // full url, or None if none found
    string base_url; // base url or None if none found

    citation(const string &src);
    string get_url(); // return base_url
    string get_author(); // return author
    void remove_url(); // set url and base_url to "None"
    void remove_author(); // set author to "None"

private:
    void read_url(const string &src,int start_from); // parses the url 
    void read_author(const string &src); // parses the author 
};


class wikipage 
{
    private:
        // Get page sections
        void get_title(string &page);
        void get_namespace(string &page);
        void get_redirect(string &page);
        void get_timestamp(string &page);
        void get_contributor(string &page);
        void get_comment(string &page);
        void get_text(string &page);
        void get_ID(string &page);

        // Get text sections
        void read_categories();
        void read_links();
        void read_image_count();
        void get_quality();
        
        void get_importance();
        void get_instance();
        void get_daily_views();
        void get_instance_of();
        void read_citations();
        void flatten_citations();

        // Text methods
        void clean_text();
        void percent_decoding();
        void remove_templates();
        void remove_html_elements();
        void remove_file_references();
        void remove_image_references();

        // ensure that all fields fit json formatting
        void make_fields_kosher();

    public:
        // Page sections
        string title;
        string ns;
        string redirect;
        string timestamp;
        string contributor;
        string comment;
        string text;
        unsigned ID;

        // new attributes (added for json output)
        vector<citation> citations;
        string importance;
        string instance;
        string quality;
        string daily_views;

        // Text sections
        vector<string> categories; 
        vector<string> links;
        unsigned short image_count; 

    	// Constructor
        wikipage(string page);
        void save(ofstream &file);
        bool save_json(ofstream &file);

        // Boolean checks
        bool is_redirect();
        bool is_disambig();
        bool is_article();
        bool is_talk_page();

        bool has_categories();
        bool has_links();


        // Stream I/O
        friend ostream& operator<<(ostream& os, wikipage& wp);
};

#define WIKIPAGE
#endif