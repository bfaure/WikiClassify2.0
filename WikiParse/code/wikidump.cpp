#include "wikidump.h"
#include "wikipage.h"
#include "string_utils.h"

wikidump::wikidump(string &path) {
    dump_input  = ifstream(path, ifstream::binary);
    if (dump_input.is_open()) {
        dump_size = ifstream(path, ifstream::ate | ifstream::binary).tellg();
    }
    else {
        cout<<"Could not open dump! ("<<path<<")"<<endl;
    }
}

unsigned wikidump::save_buffer(const string &str) {
    string tag1 = "\n  <page>\n";
    string tag2 = "\n  </page>\n";
    size_t p1 = str.find(tag1);
    size_t p2;
    while (p1!=string::npos) {
        p1 += tag1.length();
        p2  = str.find(tag2, p1);
        if (p2!=string::npos) {
            articles_read++;
            wikipage wp(str.substr(p1, p2-p1));
            wp.save(dump_output);
            p1 = str.find(tag1, p2+tag2.length());
        }
        else {
            return p1;
        }
    }
    return p2;
}

void wikidump::read(string output_directory) {

    string document_path      = output_directory+"/documents.tsv";
    string category_name_path = output_directory+"/category_names.tsv";
    string category_tree_path = output_directory+"/category_tree.tsv";

    dump_output = ofstream(document_path);
    
    articles_read  = 0;
    
    streampos offset;
    const streampos buffer_size = 2000000;
    char buffer[(unsigned)buffer_size];
    
    time_t start_time = time(0);
    int display_refresh_rate = 5; // every 5 seconds, clear the output line

    while (dump_input.read(buffer, sizeof(buffer))) {

        offset = save_buffer(buffer);
        dump_input.seekg(dump_input.tellg()-buffer_size+offset);
    
        if (time(0)-start_time % display_refresh_rate == 0) {
            cout.flush();
            cout<<"\r";
            cout.flush();
        }
    
        cout.flush();
        cout<<"\r"<<(int)100.0*dump_input.tellg()/dump_size<<"% done, "<<time(0)-start_time<<" seconds elapsed, "<<articles_read<<" articles parsed.";
        cout.flush();
    }
    
    cout<<endl;
}