#include "code/wikidump.h"
#include <unistd.h>
#include <string>

string email_to = "bfaure23@gmail.com"; // change this to your email


int main(int argc, const char * argv[]) {

	if (argc == 2) 
	{
        wikidump dump(argv[1]); // Specify where the dump is, given first argument
        dump.read(email_to); 
        return 0;
	}
	
	else
	{
		//string filename = "data/input/simplewiki-latest-pages-articles.xml";
		string filename = "data/input/enwiki-latest-pages-articles.xml";
		//string filename = "data/input/simplewiki-latest-pages-meta-current.xml";
		wikidump dump(filename);
		dump.read(email_to);
		return 1;
	}
}
