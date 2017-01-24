#include "wikidump.h"
#include "wikipage.h"
#include "string_utils.h"

ofstream dump_output("documents.txt");

void read_page(string page) {
    //cout<<"Reading page!"<<endl;
    wikipage wp(page);
    wp.save(dump_output);
}

wikidump::wikidump(string path) {
    dump_input  = ifstream(path, ifstream::binary);
    if (dump_input.is_open()) {
        dump_size   = ifstream(path, ifstream::ate | ifstream::binary).tellg();
    }
    else {
        cout<<"Could not open dump!"<<endl;
    }
}

void wikidump::read() {
    streampos offset;
    streampos buffer_size = 5000000;
    char     buffer[(unsigned)buffer_size];
    while (dump_input.read(buffer, sizeof(buffer))) {
        offset = parse_all(buffer, "\n  <page>\n", "\n  </page>\n", read_page);
        dump_input.seekg(dump_input.tellg()-buffer_size+offset);
        cout<<"\r"<<(int)100.0*dump_input.tellg()/dump_size<<"% done!";
    }
}