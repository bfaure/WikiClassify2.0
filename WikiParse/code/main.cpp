#include "wikidump.h"
#include <unistd.h>
#include <string>

int main(int argc, const char * argv[]) {
	if (argc == 3) {
		string dump_path        = argv[1];
		string cutoff_date      = argv[2];
        wikidump dump(dump_path, cutoff_date);
        dump.read();
        return 0;
	}
	else {
		return 1;
	}
}