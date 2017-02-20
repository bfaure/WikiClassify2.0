#include "wikidump.h"
#include <unistd.h>
#include <string>

int main(int argc, const char * argv[]) {
	if (argc == 3) {
		string dump_path = argv[1];
		string output_directory = argv[2];
		cout<<dump_path<<endl;
		cout<<output_directory<<endl;
        wikidump dump(dump_path);
        dump.read(output_directory);
        return 0;
	}
	else {
		return 1;
	}
}