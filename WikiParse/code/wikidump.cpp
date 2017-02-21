#include "wikidump.h"
#include "wikipage.h"
#include "string_utils.h"

wikidump::wikidump(string &path, string &output_directory) {
    dump_input  = ifstream(path, ifstream::binary);
    if (dump_input.is_open()) {
        dump_size = ifstream(path, ifstream::ate|ifstream::binary).tellg();
    }
    else {
        cout<<"Could not open dump! ("<<path<<")"<<endl;
    }
    database db(output_directory);
    articles_read = 0;
}

void wikidump::read() {
    streampos offset;
    const streampos buffer_size = 2000000;
    char buffer[(unsigned)buffer_size];
    time_t start_time = time(0);
    while (dump_input.read(buffer, sizeof(buffer))) {
        offset = save_buffer(buffer);
        dump_input.seekg(dump_input.tellg()-buffer_size+offset);
        cout.flush();
        cout<<"\r"<<(int)100.0*dump_input.tellg()/dump_size<<"% done, "<<time(0)-start_time<<" seconds elapsed, "<<articles_read<<" articles parsed.";
    }
    cout<<endl;
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
            wikipage wp(str.substr(p1, p2-p1));
            db.save(wp);
            articles_read++;
            p1 = str.find(tag1, p2+tag2.length());
        }
        else {
            return p1;
        }
    }
    return p2;
}

database::database() {

}

database::database(string &output_directory) {

}

void database::save(wikipage &wp) {
    if (wp.is_article()) {
        if (!wp.text.empty()) {
            kosher(wp.title);
            kosher(wp.categories);
            for (int i=0; i<wp.categories.size(); i++) {
            }
        }
    }
}

void kosher(string &field) {
    replace_target(field,"\n"," ");
    replace_target(field,"\t"," ");
    replace_target(field,"\"","\\\"");
    replace_target(field,"\\\\\"","\\\"");
    while (field[field.length()-1] == '\\') {
        field.erase(field.length()-1);
    }
}

void kosher(vector<string> &fields) {
    for (int i=0; i<fields.size(); i++) {
        kosher(fields[i]);
    }
}