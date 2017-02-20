#include "wikidump.h"
#include "wikipage.h"
#include "string_utils.h"

void read_page(string page, ofstream &dump_output, unsigned long long &articles_saved) {
    wikipage wp(page);
    wp.save(dump_output);
    articles_saved++;
}

wikidump::wikidump(string &path) {
    dump_input  = ifstream(path, ifstream::binary);
    if (dump_input.is_open()) {
        dump_size = ifstream(path, ifstream::ate | ifstream::binary).tellg();
    }
    else {
        cout<<"Could not open dump! ("<<path<<")"<<endl;
    }
}

void wikidump::read(string output_directory) {

    string document_path      = output_directory+"/documents.tsv";
    string category_name_path = output_directory+"/category_names.tsv";
    string category_tree_path = output_directory+"/category_tree.tsv";

    dump_output = ofstream(document_path);
    
    articles_read  = 0;
    articles_saved = 0;
    
    streampos offset;
    const streampos buffer_size = 2000000;
    char buffer[(unsigned)buffer_size];
    
    time_t start_time = time(0);
    int display_refresh_rate = 5; // every 5 seconds, clear the output line

    while (dump_input.read(buffer, sizeof(buffer))) {

        offset = save_all(buffer, "\n  <page>\n", "\n  </page>\n", read_page, dump_output, articles_read, articles_saved);
        dump_input.seekg(dump_input.tellg()-buffer_size+offset);
    
        if (time(0)-start_time % display_refresh_rate == 0) {
            cout.flush();
            cout<<"\r";
            cout.flush();
        }
    
        cout.flush();
        cout<<"\r"<<(int)100.0*dump_input.tellg()/dump_size<<"% done, "<<time(0)-start_time<<" seconds elapsed, "<<articles_read<<" articles read, "<<articles_read-articles_saved<<" articles were not saved";
        cout.flush();
    }
    
    cout<<endl;
}