#include "wikipage.h"
#include "string_utils.h"
#include "wikitext.h"

wikipage::wikipage(string page) {
    read_title(page);
    read_namespace(page);
    read_ID(page);
    if (is_article()) {
        read_redirect(page);
        if (!is_redirect()) {
            read_timestamp(page); 
            read_contributor(page);
            if (!is_disambig()) {
                read_text(page);
            }
        }
    }
    if (is_category()) {
        read_timestamp(page); 
        read_contributor(page);
        read_text(page);
    }
}

void kosher(string &field) {
    decode_text(field);
    replace_target(field,"\n"," ");
    replace_target(field,"\t"," ");
    remove_target(field,"\"");
    string target = "&lt;";
    string endtarget = "&gt;";
    remove_between(field,target,endtarget);
    remove_target(field,"'");
    trim(field);
    remove_target(field,"\\");
    decode_text(field);
}

void kosher(vector<string> &fields) {
    for (int i=0; i<fields.size(); i++) {
        kosher(fields[i]);
    }
}

//Save function (save to file)
void wikipage::save(ofstream &file) {
    if (!text.empty()) {
        for(int i=0; i<categories.size(); i++) {
            if (i) {
                file<<'\t';
            }
            file<<categories[i];
        }
        file<<"\t";
        kosher(text);
        kosher(categories);
        file<<text<<'\n';
    }
}

void wikipage::read_title(string &page) {
    parse(page, "    <title>", "</title>\n    ", title);

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

void wikipage::read_namespace(string &page) {
    parse(page, "    <ns>", "</ns>\n    ", ns);
}

void wikipage::read_ID(string &page) {
    string ID_str; 
    parse(page, "    <id>", "</id>\n    ", ID_str);
    ID=stoi(ID_str);
}

void wikipage::read_redirect(string &page) {
    parse(page, "    <redirect title=\"", "\" />", redirect);
}

void wikipage::read_timestamp(string &page) {
    parse(page, "      <timestamp>", "</timestamp>\n      ", timestamp);
}

void wikipage::read_contributor(string &page) {
    parse(page,"      <contributor>\n","      </contributor>\n",contributor);
    if (contributor.find("<ip>")!=string::npos) {
        parse(contributor,"        <ip>","</ip>\n",contributor);
    }
    else {
        if (contributor.find("<username>")!=string::npos) {
            parse(contributor,"        <username>","</username>\n",contributor);
        }
        else {
            contributor = "";
        }
    }
}

void wikipage::read_text(string &page) {
    string page_text;
    parse(page,"      <text xml:space=\"preserve\">","</text>\n      ",page_text);
    
    wikitext wt(page_text);
    text       = wt.text;
    categories = wt.categories;
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