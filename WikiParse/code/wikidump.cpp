#include "wikidump.h"
#include "wikipage.h"
#include "string_utils.h"

wikidump::wikidump(string &path, string &cutoff_date) {
    dump_input = ifstream(path,ifstream::binary);
    if (dump_input.is_open()) {
        dump_size = ifstream(path,ifstream::ate|ifstream::binary).tellg();
    }
    else {
        cout<<"Could not open dump! ("<<path<<")\n";
    }
    cutoff_year  = stoi(cutoff_date.substr(0,4));
    cutoff_month = stoi(cutoff_date.substr(4,2));
    cutoff_day   = stoi(cutoff_date.substr(6,2));
}

void wikidump::read() {
    //int bzError;
    //char buf[4096];
    //BZFILE *bzf = BZ2_bzReadOpen(&bzError, file_path.c_str(), 0, 0, NULL, 0);
    //while (bzError == BZ_OK) {
    //  int nread = BZ2_bzRead(&bzError, bzf, buf, sizeof buf);
    //  if (bzError == BZ_OK || bzError == BZ_STREAM_END) {
    //    continue;
    //  }
    //}
    //BZ2_bzReadClose(&bzError, bzf);
    articles_read = 0;
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
    cout<<"\n";
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
            if (wp.is_after(cutoff_year, cutoff_month, cutoff_day)) {
                wp.read();
                dump_output.save_page(wp);
            }
//            wikipage wp(str);
//            titles[wp.title] = wp.id;
//            if (!wp.redirect.empty()) {
//                redirects[wp.title] = wp.redirect;
//            }
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
    titles.open("titles.tsv",ofstream::out|ofstream::trunc|ofstream::binary);
    redirects.open("redirects.tsv",ofstream::out|ofstream::trunc|ofstream::binary);
    text.open("text.tsv",ofstream::out|ofstream::trunc|ofstream::binary);
    categories.open("categories.tsv",ofstream::out|ofstream::trunc|ofstream::binary);
    links.open("links.tsv",ofstream::out|ofstream::trunc|ofstream::binary);
    authors.open("authors.tsv",ofstream::out|ofstream::trunc|ofstream::binary);
    domains.open("domains.tsv",ofstream::out|ofstream::trunc|ofstream::binary);
    //importance.open(output_directory+"/importance.tsv",ofstream::out|ofstream::trunc|ofstream::binary);
    //quality.open(output_directory+"/quality.tsv",ofstream::out|ofstream::trunc|ofstream::binary);
    //problems.open(output_directory+"/problems.tsv",ofstream::out|ofstream::trunc|ofstream::binary);
    category_parents.open("category_parents.tsv",ofstream::out|ofstream::trunc|ofstream::binary);
}

void database::save_page(wikipage &wp) {
    titles<<wp.id<<'\t'<<wp.title<<'\n';
    if (wp.is_article()) {
        if (!wp.text.empty()) {
            text<<wp.id<<'\t'<<wp.text<<'\n';

            categories<<wp.id<<'\t';;
            for (int i=0; i<wp.categories.size(); i++) {
                categories<<wp.categories[i]<<' ';
            }
            categories<<'\n';

            links<<wp.id<<'\t';;
            for (int i=0; i<wp.links.size(); i++) {
                links<<wp.links[i]<<' ';
            }
            links<<'\n';

            authors<<wp.id<<'\t';;
            for (int i=0; i<wp.authors.size(); i++) {
                authors<<wp.authors[i]<<' ';
            }
            authors<<'\n';

            domains<<wp.id<<'\t';;
            for (int i=0; i<wp.domains.size(); i++) {
                domains<<wp.domains[i]<<' ';
            }
            domains<<'\n';
        }
    }
    if (wp.is_category()) {

        category_parents<<wp.id<<'\t';
        for (int i=0; i<wp.categories.size(); i++) {
            category_parents<<wp.categories[i]<<' ';
        }
        category_parents<<'\n';
    }
}