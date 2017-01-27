#include "wikidump.h"
#include "wikipage.h"
#include "string_utils.h"
#include <time.h>

//ofstream dump_output("documents.txt");
ofstream dump_output("documents.json");


vector<wikipage> save_buffer;
int save_buffer_length_target = 10000;

void read_page(string page) {
    //cout<<"Reading page!"<<endl;
    wikipage wp(page);
    //wp.save(dump_output);
    wp.save_json(dump_output);
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

void wikidump::read() {
    articles_read = 0;

    streampos offset; 
    const streampos buffer_size = 2000000;
    char     buffer[(unsigned)buffer_size];
    
    time_t start_time = time(0);
    int display_refresh_rate = 5; // every 5 seconds, clear the output line

    dump_output<<"{\n";
    while (dump_input.read(buffer, sizeof(buffer))) {

        offset = parse_all(buffer, "\n  <page>\n", "\n  </page>\n", read_page, articles_read);
        dump_input.seekg(dump_input.tellg()-buffer_size+offset);
        if (time(0)-start_time % display_refresh_rate == 0)
        {
            cout.flush();
            cout<<"\r                                                                                         ";
            cout.flush();
        }
        cout.flush();
        cout<<"\r"<<(int)100.0*dump_input.tellg()/dump_size<<"% done, "<<time(0)-start_time<<" seconds elapsed, "<<articles_read<<" articles read";
        cout.flush();
    }
    cout<<"\n"; // to preserve the display line
    dump_output<<"\n}";
}