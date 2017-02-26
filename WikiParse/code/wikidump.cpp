#include "wikidump.h"
#include "wikipage.h"
#include "string_utils.h"

wikidump::wikidump(string &path, string &output_directory, string &cutoff_date) {

    dump_input = ifstream(path, ifstream::binary);

    if (dump_input.is_open()) {
        dump_size = ifstream(path, ifstream::ate|ifstream::binary).tellg();
    }
    else {
        cout<<"Could not open dump! ("<<path<<")\n";
    }

    articles_read = 0;

    cutoff_year  = stoi(cutoff_date.substr(0,4));
    cutoff_month = stoi(cutoff_date.substr(4,2));
    cutoff_day   = stoi(cutoff_date.substr(6,2));

    article_titles.open(output_directory+"/article_titles.txt",std::ofstream::out|std::ofstream::trunc);
    article_revisions.open(output_directory+"/article_revisions.txt",std::ofstream::out|std::ofstream::trunc);
    article_revision_text.open(output_directory+"/article_revision_text.txt",std::ofstream::out|std::ofstream::trunc);
    article_revision_categories.open(output_directory+"/article_revision_categories.txt",std::ofstream::out|std::ofstream::trunc);
    article_revision_cited_authors.open(output_directory+"/article_revision_cited_authors.txt",std::ofstream::out|std::ofstream::trunc);
    article_revision_cited_domains.open(output_directory+"/article_revision_cited_domains.txt",std::ofstream::out|std::ofstream::trunc);

    category_titles.open(output_directory+"/category_names.txt",std::ofstream::out|std::ofstream::trunc);
    category_revisions.open(output_directory+"/category_revisions.txt",std::ofstream::out|std::ofstream::trunc);
    category_revision_parents.open(output_directory+"/category_revision_parents.txt",std::ofstream::out|std::ofstream::trunc);
    //article_importance.open(output_directory+"/article_importance.txt",std::ofstream::out|std::ofstream::trunc);
    //article_quality.open(output_directory+"/article_quality.txt",std::ofstream::out|std::ofstream::trunc);
    //article_problems.open(output_directory+"/article_problems.txt",std::ofstream::out|std::ofstream::trunc);
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
                save_page(wp);
                articles_read++;
            }
            p1 = str.find(tag1, p2+tag2.length());
        }
        else {
            return p1;
        }
    }
    return p2;
}

void wikidump::save_page(wikipage &wp) {
    if (wp.is_article()) {
        if (!wp.revision_text.empty()) {
            article_titles<<wp.id<<'\t'<<wp.title<<'\n';
            article_revisions<<wp.revision<<'\t'<<wp.id<<'\n';
            article_revision_text<<wp.revision<<'\t'<<wp.revision_text<<'\n';

            article_revision_categories<<wp.revision;
            for (int i=0; i<wp.revision_categories.size(); i++) {
                article_revision_categories<<'\t'<<wp.revision_categories[i];
            }
            article_revision_categories<<'\n';

            article_revision_cited_authors<<wp.revision;
            for (int i=0; i<wp.revision_cited_authors.size(); i++) {
                article_revision_cited_authors<<'\t'<<wp.revision_cited_authors[i];
            }
            article_revision_cited_authors<<'\n';

            article_revision_cited_domains<<wp.revision;
            for (int i=0; i<wp.revision_cited_domains.size(); i++) {
                article_revision_cited_domains<<'\t'<<wp.revision_cited_domains[i];
            }
            article_revision_cited_domains<<'\n';
        }
    }
    if (wp.is_category()) {
        category_titles<<wp.id<<'\t'<<wp.title<<'\n';
        category_revisions<<wp.revision<<'\t'<<wp.id<<'\n';

        category_revision_parents<<wp.revision;
        for (int i=0; i<wp.revision_categories.size(); i++) {
            category_revision_parents<<'\t'<<wp.revision_categories[i];
        }
        category_revision_parents<<'\n';
    }
}