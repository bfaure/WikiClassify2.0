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

void wikidump::read(bool build_keys) {
    if (build_keys) {
        cout<<"Building keys...\n";
    }
    else {
        cout<<"Reading dump...\n";
    }
    articles_read = 0;
    streampos offset;
    const streampos buffer_size = 2000000;
    char buffer[(unsigned)buffer_size];
    time_t start_time = time(0);
    while (dump_input.read(buffer, sizeof(buffer))) {
        offset = save_buffer(buffer, build_keys);
        dump_input.seekg(dump_input.tellg()-buffer_size+offset);
        cout.flush();
        cout<<"\r"<<(int)100.0*dump_input.tellg()/dump_size<<"% done, "<<time(0)-start_time<<" seconds elapsed, "<<articles_read<<" articles parsed.";
    }
    dump_input.clear();
    dump_input.seekg(0, dump_input.beg);
    cout<<"\n";
    if (build_keys) {
        save_keys();
        connect_database();
        read(false);
    }
}

unsigned wikidump::save_buffer(const string &str, bool build_keys) {
    string tag1 = "<page>";
    string tag2 = "</page>";
    size_t p1 = str.find(tag1);
    size_t p2;
    while (p1!=string::npos) {
        p1 += tag1.length();
        p2  = str.find(tag2, p1);
        if (p2!=string::npos) {
            if (build_keys) {
                wikipage wp(str.substr(p1, p2-p1));
                if (wp.redirect.empty()) {
                    title_map[wp.title] = wp.id;
                }
                else {
                    redirect_map[wp.title] = wp.redirect;
                }
            }
            else {
                wikipage wp(str.substr(p1, p2-p1));
                if (wp.is_after(cutoff_year, cutoff_month, cutoff_day)) {
                    wp.read();
                    save_page(wp);
                }
            }
            articles_read++;
            p1 = str.find(tag1, p2+tag2.length());
        }
        else {
            return p1-tag1.length();
        }
    }
    return p2;
}

void wikidump::save_keys() {
    titles.open("titles.tsv");
    for (auto& kv:title_map) {
        titles<<kv.second<<"\t"<<kv.first<<"\n";
    }
    redirects.open("redirects.tsv");
    for (auto& kv:redirect_map) {
        if (title_map.find(kv.second) != title_map.end()) {
            redirects<<kv.first<<"\t"<<title_map[kv.second]<<"\n";
        }
    }
}

void wikidump::connect_database() {
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

void wikidump::save_page(wikipage &wp) {
    if (wp.is_article()) {
        text<<wp.id<<'\t'<<wp.text<<'\n';

        categories<<wp.id<<'\t';;
        for (auto& category:wp.categories) {
            if (title_map.find(category) != title_map.end()) {
                categories<<title_map[category]<<' ';
            }
        }
        categories<<'\n';

        links<<wp.id<<'\t';
        for (auto& link:wp.links) {
            if (redirect_map.find(link) != redirect_map.end()) {
                link = redirect_map[link];
            }
            if (title_map.find(link) != title_map.end()) {
                links<<title_map[link]<<' ';
            }
        }
        links<<'\n';

//        authors<<wp.id<<'\t';;
//        for (int i=0; i<wp.authors.size(); i++) {
//            authors<<wp.authors[i]<<' ';
//        }
//        authors<<'\n';
//
//        domains<<wp.id<<'\t';;
//        for (int i=0; i<wp.domains.size(); i++) {
//            domains<<wp.domains[i]<<' ';
//        }
//        domains<<'\n';
    }
//    if (wp.is_category()) {
//
//        category_parents<<wp.id<<'\t';;
//        for (auto& category:wp.categories) {
//            if (title_map.find(category) != title_map.end()) {
//                category_parents<<title_map[category]<<"\n";
//            }
//        }
//        categories<<'\n';
//    }
}