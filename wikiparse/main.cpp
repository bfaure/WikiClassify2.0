#include "wikidump.h"

int main(int argc, const char * argv[]) {
	if (argc == 2) {
        wikidump dump(argv[1]); // Specify where the dump is, given first argument
        dump.read();            // Start scraping
        return 0;
	}
}