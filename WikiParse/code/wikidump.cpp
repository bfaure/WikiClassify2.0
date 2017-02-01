#include "wikidump.h"
#include "wikipage.h"
#include "string_utils.h"
#include <time.h>
#include <stdlib.h>

ofstream dump_output;
unsigned long articles_saved;
string file_type;

void read_page(string page) {
    wikipage wp(page,file_type);
    if (file_type=="txt")
    {
        if(wp.save_txt(dump_output))
        {
            articles_saved++;
            return;
        }
    }
    else
    {
        if(wp.save_json(dump_output))
        {
            articles_saved++;
        }
    }
}

wikidump::wikidump(string path) {
    dump_input  = ifstream(path, ifstream::binary);
    if (dump_input.is_open()) {
        dump_size   = ifstream(path, ifstream::ate | ifstream::binary).tellg();
    }
    else {
        cout<<"Could not open dump! ("<<path<<")"<<endl;
    }
}

void wikidump::read()
{
    read("json");
}

void wikidump::read(string destination) 
{
    if (destination.find(".json")!=string::npos)
    {
            file_type = "json";
            dump_output.open(destination);
    }
    else
    {
        if (destination.find(".txt")!=string::npos)
        {
            file_type = ".txt";
            dump_output.open(destination);
        }
        else
        {
            cout<<"File type for destination not recognized!\n";
            return;
        }
    }

    articles_read = 0; // total number of articles parsed
    articles_saved = 0; // total number saved

    streampos offset; 
    const streampos buffer_size = 2000000;
    char     buffer[(unsigned)buffer_size];
    
    time_t start_time = time(0);
    int display_refresh_rate = 5; // every 5 seconds, clear the output line
    
    if (file_type=="json"){dump_output<<"{\n";}
    
    while (dump_input.read(buffer, sizeof(buffer)))
    {
        offset = parse_all(buffer, "\n  <page>\n", "\n  </page>\n", read_page, articles_read);
        dump_input.seekg(dump_input.tellg()-buffer_size+offset);
        if (time(0)-start_time % display_refresh_rate == 0)
        {
            cout.flush();
            cout<<"\r                                                                                         ";
            cout.flush();
        }
        cout.flush();
        cout<<"\r"<<(int)100.0*dump_input.tellg()/dump_size<<"% done, "<<time(0)-start_time<<" seconds elapsed, "<<articles_read<<" articles read, "<<articles_saved<<" articles saved";
        cout.flush();
    }

    cout<<"\n"; // to preserve the display line
    if (file_type=="json"){dump_output<<"\n}";}
}