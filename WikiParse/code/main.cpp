#include "wikidump.h"
#include <unistd.h>
#include <string>

int main(int argc, const char * argv[]) 
{
	
	if (argc == 3) 
	{
		string dump_path        = argv[1];
		string destination_path = argv[2];
        wikidump dump(dump_path);
        dump.read(destination_path); 
        return 0;
	}
	
	else
	{
		return 1;
	}
}