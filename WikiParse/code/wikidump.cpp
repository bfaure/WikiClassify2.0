#include "wikidump.h"
#include "wikipage.h"
#include "string_utils.h"
#include <time.h>
#include <stdlib.h>

//ofstream dump_output("documents.txt");
ofstream dump_output("documents.json");
unsigned long articles_saved;

//vector<wikipage> save_buffer;
//int save_buffer_length_target = 10000;

void read_page(string page) {
    //cout<<"Reading page!"<<endl;
    wikipage wp(page);
    //wp.save(dump_output);
    if(wp.save_json(dump_output))
    {
        articles_saved++;
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

void send_email(string email_address, string body)
{
    string command_call = "python code/email_agent.py "+email_address+" "+body;
    system(command_call.c_str());
}

void wikidump::read()
{
    read("None");
}

void wikidump::read(string email_address) {
    articles_read = 0;
    articles_saved = 0;

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
        cout<<"\r"<<(int)100.0*dump_input.tellg()/dump_size<<"% done, "<<time(0)-start_time<<" seconds elapsed, "<<articles_read<<" articles read, "<<articles_saved<<" articles saved";
        cout.flush();
    }
    cout<<"\n"; // to preserve the display line
    dump_output<<"\n}";
    

    if (email_address!="None")
    {
        string email_body = "articles_read-"+to_string(articles_read)+"+articles_saved-"+to_string(articles_saved)+"+seconds-"+to_string(time(0)-start_time);
        send_email(email_address,email_body);
    }
}