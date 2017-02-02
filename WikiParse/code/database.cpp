#include "database.h"

database::database() {

}

bool database::create_table() {

   cout<<"Creating table..."<<endl;

   const char* sql = "CREATE TABLE ARTICLES("
                       "ID INT PRIMARY KEY NOT NULL,"
                       "TITLE TEXT NOT NULL,"
                       "NS TEXT NOT NULL,"
                       "CONTRIBUTOR TEXT NOT NULL,"
                       "SIZE INT NOT NULL"
                     ");";

   return sqlite3_exec(db, sql, NULL, NULL, NULL);

}

database::database(string path) {
   if (sqlite3_open("test.db", &db)) {
      cout<<"Database error: "<<sqlite3_errmsg(db)<<endl;
   }
   else {
      cout<<"Database opened!"<<endl;
      if (create_table()) {
          cout<<"Table created!"<<endl;
      }
      else {
          cout<<"Table could not be created!"<<endl;
      }
   }
}

database::~database() {
   sqlite3_close(db);
}

bool database::add() {
   return true;
}