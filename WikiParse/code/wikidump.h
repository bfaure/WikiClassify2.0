#ifndef WIKIDUMP

/* Standard Imports */

#include <iostream>
using std::cout;
using std::ofstream;

#include <fstream>
using std::ifstream;
using std::ofstream;
using std::streampos;

#include <string>
using std::string;

#include <map>
using std::map;

#include <time.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

/* Local Imports */
#include "wikipage.h"
#include "string_utils.h"

// For accessing database
#include <pqxx/pqxx>

class wikidump {
    private:

        ofstream titles;
        ofstream redirects;
        ofstream text;
        ofstream categories;
        ofstream links;
        ofstream authors;
        ofstream domains;
        //ofstream quality;
        //ofstream importance;
        //ofstream problems;
        ofstream category_parents;

        ifstream dump_input;
        ifstream::pos_type dump_size;
        unsigned articles_read;
        unsigned cutoff_year;
        unsigned cutoff_month;
        unsigned cutoff_day;

        map<string, unsigned> title_map;
        map<string, string> redirect_map;

        pqxx::connection *conn;

        string  server_password;
        bool    connected_to_server;
        int     num_sent_to_server;
        int     server_capacity; // bytes
        bool    replace_server_duplicates;

        int                 server_write_buffer_size;
        vector<wikipage>    server_write_buffer;

    public:
        wikidump(string &path, string &cutoff_date, string password);
        void connect_to_server();

        void read(bool build_keys=true);
        unsigned save_buffer(const string &str,bool build_keys);
        void tokenize_page(wikipage& wp);
        void save_keys();

        void connect_database();
        void save_page(wikipage &wp);
        void server_write();
        int get_server_used_bytes();
};


#define WIKIDUMP
#endif