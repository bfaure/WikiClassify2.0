#include "wikidump.h"
#include <unistd.h>
#include <string>
#include <iostream>

int main(int argc, const char * argv[]) {
	if (argc == 8)
	{
		string dump_path    = argv[1];
		string cutoff_date  = argv[2];
		string password 		= argv[3];
		string host 				= argv[4];
		string username 		= argv[5];
		string port 				= argv[6];
		string dbname 			= argv[7];
    wikidump dump(dump_path, cutoff_date, password, host, username, port, dbname);
    dump.read();
    return 0;
	}
	else
	{
		if (argc == 4)
		{
			string dump_path    = argv[1];
			string cutoff_date  = argv[2];
			string password 		= argv[3];
			wikidump dump(dump_path, cutoff_date, "NONE","NONE","NONE","NONE","NONE");
			dump.read();
			return 2;
		}
		else
		{
			std::cout<<"main.cpp: Incorrect number of arguments: <dump_path> <cutoff_date> <password> <host> <username> <port> <dbname>\n";
			return 1;
		}
	}
}
