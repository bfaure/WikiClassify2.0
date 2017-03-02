#include "wikipage.h"
#include "string_utils.h"
#include "wikitext.h"

wikipage::wikipage(string dump_page) {
    this->dump_page = dump_page;
    read_title();
    read_namespace();
    read_id();
    read_revision();
    read_redirect();
    read_timestamp();
}

void wikipage::read() {
    read_text();
    make_kosher();
}

void wikipage::make_kosher() {
    // Clean, just to make sure
    kosher(title);
    kosher(ns);
    kosher(redirect);
    // Clean items within text
    kosher(revision_text);
    kosher(revision_importance);
    kosher(revision_quality);
    kosher(revision_categories); 
    kosher(revision_links);
    kosher(revision_cited_domains);
    kosher(revision_cited_authors);
    kosher(revision_problems);
}

void kosher(vector<string> &fields) {
    for (int i=0; i<fields.size(); i++) {
        kosher(fields[i]);
    }
}

void kosher(string &field) {
    replace_target(field,"\n"," ");
    replace_target(field,"\t"," ");
}

void wikipage::read_title() {
    parse(dump_page, "    <title>", "</title>\n    ", title);

    // Fix Title
    bool condition = true;
    while(condition){
        size_t location = title.find("/");
        if (location != string::npos){
            title.replace(location, 1, ".");
        }
        else {
            condition=false;
        }
    }
    condition = true;
    while(condition){
        size_t location = title.find(" ");
        if (location != string::npos){
            title.replace(location, 1, "_");
        }
        else {
            condition=false;
        }
    }
}

void wikipage::read_namespace() {
    parse(dump_page, "    <ns>", "</ns>\n    ", ns);
}

void wikipage::read_id() {
    string id_str; 
    parse(dump_page, "    <id>", "</id>\n    ", id_str);
    id = stoi(id_str);
}

void wikipage::read_revision() {
    string revision_str; 
    parse(dump_page, "<revision>\n      <id>", "</id>\n      ", revision_str);
    revision = stol(revision_str);
}

void wikipage::read_redirect() {
    if (is_article()) {
        parse(dump_page, "    <redirect title=\"", "\" />", redirect);
        replace_target(redirect," ","_");
    }
}

void wikipage::read_timestamp() {
    string timestamp;
    parse(dump_page, "      <timestamp>", "</timestamp>\n      ", timestamp);
    revision_year  = stoi(timestamp.substr(0,4));
    revision_month = stoi(timestamp.substr(5,2));
    revision_day   = stoi(timestamp.substr(8,2));
}

void wikipage::read_text() {
    string page_text;
    parse(dump_page,"      <text xml:space=\"preserve\">","</text>\n      ",page_text);
    wikitext wt(page_text);
    if (is_article() && !is_redirect()) {
        wt.read_article();
        revision_text          = wt.text;
        revision_categories    = wt.categories;
        revision_links         = wt.links;
        revision_cited_domains = wt.cited_domains;
        revision_cited_authors = wt.cited_authors;
        revision_problems      = wt.problems;
    }
    else if (is_category()) {
        wt.read_category();
        revision_categories    = wt.categories;
    }
    else if (is_talk()) {
        wt.read_talk();
        revision_importance = wt.importance;
        revision_quality    = wt.quality;
    }
}

bool wikipage::is_after(unsigned int &year, unsigned int &month, unsigned int &day) {
    if (revision_year>year) {
        return true;
    }
    else if (revision_year==year&&revision_month>month) {
        return true;
    }
    else if (revision_day==month&&revision_day>day) {
        return true;
    }
    return false;
}

bool wikipage::is_redirect() {
    return redirect.length();
}

bool wikipage::is_disambig() {
    return count_string(title, "(disambiguation)");
}

bool wikipage::is_article() {
    return (ns=="0");
}

bool wikipage::is_talk() {
    return (ns=="1");
}

bool wikipage::is_category() {
    return (ns=="14");
}