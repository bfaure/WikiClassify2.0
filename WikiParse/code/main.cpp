#include "wikidump.h"
#include <unistd.h>
#include <string>

int main(int argc, const char * argv[]) {
	if (argc == 4) {
		string dump_path        = argv[1];
		string cutoff_date      = argv[2];
		string password 		= argv[3];
        wikidump dump(dump_path, cutoff_date, password);
        dump.read();
        return 0;
	}
	else {
		return 1;
	}
}