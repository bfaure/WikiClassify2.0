#ifndef DATABASE

/* Standard Imports */

#include <iostream>
using std::cout;
using std::endl;

#include <string>
using std::string;

#include <sqlite3.h> 

class database {
    private:
        sqlite3 *db;

    public:
        database();
        ~database();
        database(string path);
        bool create_table();
        bool add();
};

#define DATABASE
#endif