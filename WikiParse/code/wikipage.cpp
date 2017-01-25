#include "wikipage.h"
#include "string_utils.h"
#include "wikitext.h"

wikipage::wikipage(string page) {
    get_namespace(page);             // Extract page sections
    if (is_article()) {
        get_title(page);
        get_redirect(page);
        if (!is_redirect()) {
            //get_timestamp(page);
            //get_contributor(page);
            //get_comment(page);
            get_text(page);
            clean_text();
            if (!is_disambig()) {
                //read_categories();   // Interpret text
                read_links();
                //read_image_count();
            }
        }
    }
}

void wikipage::get_title(string &page) {
    parse(page, "    <title>", "</title>\n    ", title);

    // Fix Title
    bool condition = true;
    while(condition){
        size_t location = title.find("/");
        if(location != string::npos){
            title.replace(location, 1, ".");
        }
        else{
            condition=false;
        }
    }
    condition = true;
    while(condition){
        size_t location = title.find(" ");
        if(location != string::npos){
            title.replace(location, 1, "_");
        }
        else{
            condition=false;
        }
    }
}
void wikipage::get_ID(string &page) {string ID_str; parse(page, "    <id>", "</id>\n    ", ID_str);ID=stoi(ID_str);}
void wikipage::get_namespace(string &page) {parse(page, "    <ns>", "</ns>\n    ", ns);}
void wikipage::get_redirect(string &page) {parse(page, "    <redirect title=\"", "\" />\n    ", redirect);}
void wikipage::get_timestamp(string &page) {parse(page, "      <timestamp>", "</timestamp>\n      ", timestamp);}
void wikipage::get_contributor(string &page) {parse(page, "        <username>", "</username>\n        ", contributor);}
void wikipage::get_comment(string &page) {parse(page, "      <comment>", "</comment>\n      ", comment);}
void wikipage::get_text(string &page) {parse(page, "      <text xml:space=\"preserve\">", "</text>\n      ", text);}

void wikipage::read_categories() {
    parse_all(text, "[[Category:", "]]", categories);
    for (string &category:categories) {
        string::size_type pos = category.find('|');
        if (pos != string::npos) {
            category = category.substr(0, pos);
        }
    }
}
void wikipage::read_links() {
    parse_all(text, "[[", "]]", links);
    for (string &link:links) {
        if (link.find("[[")==string::npos && link.find('\n')==string::npos) {
            string source; string destination;
            string::size_type link_sep = link.find('|');
            if (link_sep != string::npos) {
                source      = link.substr(link_sep+1);
                destination = link.substr(0,link_sep);
            }
            else {
                source      = link;
                destination = link;
            }

            // Trim
            source      = trim(source);
            destination = trim(destination);
            if (!source.empty() and !destination.empty() and source.find('|') == string::npos and destination.find('\\') == string::npos) {

                // Make lowercase
                transform(source.begin(), source.end(), source.begin(), ::tolower);

                // Remove backslash character
                source.erase(remove(source.begin(), source.end(), '\\'), source.end());
            }
        }
    }
}
void wikipage::read_image_count() {
    image_count = 0;
    vector<string> image_types {".svg",".png",".jpg",".jpeg",".gif",".tiff"};
    for (string& type:image_types) {
        image_count += count_text(text, type);
    }
}

bool wikipage::is_redirect() {
    return redirect.length();
}
bool wikipage::is_disambig() {
    return count_text(text, "{{Disambiguation}}");
}
bool wikipage::is_article() {
    return (ns=="0");
}

bool wikipage::has_categories() {
    return categories.size();
}

bool wikipage::has_links() {
    return links.size();
}

ostream& operator<<(ostream& os, wikipage& wp) {

    //os<<"Namespace:\t"<<wp.ns<<"\n";
    //os<<"Title:\t\t"<<wp.title<<"\n";
    //os<<"Redirect:\t"<<wp.redirect<<"\n";
    //os<<"Timestamp:\t"<<wp.timestamp<<"\n";
    //os<<"Contributor:\t"<<wp.contributor<<"\n";
    //os<<"Comment size:\t"<<wp.comment.size()<<"\n";
    //os<<"Article size:\t"<<wp.text.size()<<"\n";
    //os<<"Links:\t\t"<<wp.links.size()<<"\n";
    //os<<"Categories:\t"<<wp.categories.size()<<"\n";
    //os<<"Pictures:\t"<<wp.image_count;

    //for (string &link:wp.links) {
    //    os<<link<<'\n';
    //}

    return os;
}

//Save function (save to file)
void wikipage::save(ofstream &file){

    //file<<"Categories:\t";
    //for(int i=0; i<categories.size(); i++){
    //    file<<categories[i]<<' ';
    //}
    if (!text.empty()) {
        file<<text<<endl;
    }
}

void wikipage::save_json(ofstream &file)
{
    // outputs in json format on a single line of the file
    if(!text.empty())
    {
        string output = "{title:\"";
        output += title+"\",namespace:\"";
        output += ns+"\",text:\"";
        output += text+"\"}\n";
        file<<output;
    }
}

void wikipage::percent_decoding() {
    replace_target(text, "&lt;", "<");
    replace_target(text, "&gt;", ">");
    replace_target(text, "&nbsp;", " ");
    replace_target(text, "&amp;", "&");
    replace_target(text, "&quot;", "\"");
    replace_target(text, "&apos;", "'");
}

void wikipage::remove_templates() {
    // remove all double bracket regions
    string open     = "{{";
    string close    = "}}";
    while(true){
        size_t location = text.find(open);
        if (location!=string::npos) {
            int openCt  = 1;
            int ct      = 0;
            remove_nested(open, close, text, location, location, openCt, ct);

            if (text=="") {
                return;

            }
            if (ct>=300) {
                return;
            }
        }
        else {
            return;
        }
    }
}

// nested type removal of [[File: ]]
void wikipage::remove_file_references(){

    string first = "[[File:";
    string begin = "[[";
    string end = "]]";

    size_t loc = 0;

    while (true)
    {
        loc = text.find(first,loc);

        if (loc==string::npos)
        {
            return;
        }

        int openct = 1;
        int ct = 0;

        remove_nested(begin,end,text,loc,loc,openct,ct);
        if (ct >= 300){
            return;
        }
    }
}

// nested type removal of [[Image: ]]
void wikipage::remove_image_references(){

    string first = "[[Image:";
    string begin = "[[";
    string end = "]]";

    size_t loc = 0;

    while (true)
    {
        loc = text.find(first,loc);

        if (loc==string::npos)
        {
            return;
        }

        int openct = 1;
        int ct = 0;

        remove_nested(begin,end,text,loc,loc,openct,ct);
        if (ct >= 300){
            return;
        }
    }
}

void wikipage::remove_html_elements() {
    string target = "<ref";
    vector<string> endtargets = {"/ref>","/>"};
    remove_between(text,target,endtargets);

    target = "<references";
    endtargets = {"/references>","/ref>","/>"};
    remove_between(text,target,endtargets);

    target = "<nowiki";
    endtargets = {"/nowiki>","/>"};
    remove_between(text,target,endtargets);

    target = "<math";
    endtargets = {"/math>","/>"};
    remove_between(text,target,endtargets);

    target = "<gallery";
    endtargets = {"/gallery>","/>"};
    remove_between(text,target,endtargets);

    target = "<hiddentext";
    endtargets = {"/hiddentext>","/>"};
    remove_between(text,target,endtargets);

    target = "<div";
    endtargets = {"/div>","/>"};
    remove_between(text,target,endtargets);

    target = "<sub";
    endtargets = {"/sub>","/>"};
    remove_between(text,target,endtargets);

    target = "<sup";
    endtargets = {"/sup>","/>"};
    remove_between(text,target,endtargets);

    target = "<blockquote";
    endtargets = {"/blockquote>","/>"};
    remove_between(text,target,endtargets);

    target = "<references";
    endtargets = {"/references>","/>"};
    remove_between(text,target,endtargets);

    target = "<gallery";
    endtargets = {"/gallery>","/>"};
    remove_between(text,target,endtargets);
}

// removes various wikitext and xml
void wikipage::clean_text(){

    percent_decoding();
    remove_templates();

    // remove all category headers
    string target = "[[Category:";
    string endtarget = "]]";
    remove_between(text, target, endtarget);

    // remove all embedded urls
    target = "[http://";
    endtarget = "]";
    remove_between(text,target,endtarget);

    // remove all content between [[File: ]]
    remove_file_references();

    // remove all content between [[Image: ]] tags
    remove_image_references();

    target = "{|";
    endtarget = "}";
    remove_between(text,target,endtarget);

    target = "<!--";
    endtarget = "-->";
    remove_between(text,target,endtarget);

    remove_html_elements();

    // remove all '''
    target = "'''";
    remove_target(text, target);

    target = "==";
    endtarget = "==";
    remove_between(text, target, endtarget);

    target = "===";
    endtarget = "===";
    remove_between(text, target, endtarget);

    replace_target(text, {"     ","    ","  "}, " ");
    remove_target(text, "\"");
    remove_target(text, "''");
    remove_target(text, "&");
    vector<string> vec{"...",".."};
    replace_target(text, vec, ".");
    replace_target(text, "=", " ");
    remove_references(text);
    remove_target(text,"#");
    remove_between(text, "(;", ")");
    remove_target(text, "—");
    remove_target(text, "()");
    replace_target(text, ".", ". ", "strict");
    replace_target(text, ".   ", ".  ", "string");

    // remove link portion of: [[this is a |test]]
    target = "[[";
    endtarget = "|";
    remove_between_r(text, target, endtarget);

    // remove all ]]
    target = "]]";
    remove_target(text, target);

    // remove all [[
    target = "[[";
    remove_target(text, target);

    // Remove all \n
    target = "\n";
    remove_target(text, target);

    text = trim(text);

    return;
}