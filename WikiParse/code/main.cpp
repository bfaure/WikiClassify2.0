#include "wikidump.h"
#include <unistd.h>
#include <string>
#include <iostream>
using std::cout;
using std::endl;

int main(int argc, const char * argv[]) {

	if (argc == 5) {

		string dump_path          = argv[1];
		string document_path      = argv[2];
		string category_name_path = argv[3];
		string category_tree_path = argv[4];

        wikidump dump(dump_path);
        //dump.read_categories(category_name_path,category_tree_path);
        dump.read_articles(document_path);
        return 0;
	}
	else {
		return 1;
	}
}