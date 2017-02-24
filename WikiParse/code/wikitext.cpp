#include "wikitext.h"
#include "string_utils.h"

wikitext::wikitext(string text) {
    read_categories(text);
    read_links(text);
    read_citations(text);
    read_text(text);
}

void wikitext::read_categories(string &text) {
    parse_all(text, "[[Category:", "]]", categories);
    vector<string> temp;
    for (string &category:categories) {
        // if the current category contains an endline we will cut the portion after the endline
        // and add it on to the temp list to deal with later. The portion before the endline
        // will be treated like a regular category.
        if (category.find("\n")!=string::npos)  {
            temp.push_back(category.substr(category.find("\n")+1));
            category = category.substr(0,category.find("\n"));
        }
        string::size_type pos = category.find('|');
        if (pos != string::npos) {
            category = category.substr(0, pos);
        }
    }
    string tag = "Category:";
    for(int i=0; i<temp.size(); i++) {
        if (temp[i].find(tag)!=string::npos) {
            categories.push_back(temp[i].substr(temp[i].find(tag)+tag.size()));
            //cout<<"Found new category: "<<temp[i].substr(temp[i].find(tag)+tag.size())<<"\n";
        }
    }
}

void wikitext::read_links(string &text) {
    parse_all(text, "[[", "]]", links);
    for (string &link:links) {
        if (link.find("[[")==string::npos && link.find("\n")==string::npos) {
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

void wikitext::read_citations(string &text) {

    vector<string> citations;
    string endtarget = "}}";

    string target = "{{cite";
    parse_all(text,target,endtarget,citations);

    target = "{{Citation";
    parse_all(text,target,endtarget,citations);

    read_cited_domains(citations);
    read_cited_authors(citations);
}

void wikitext::read_cited_domains(vector<string> &citations) {
    for (int i=0; i<citations.size(); i++) {
        string domain;
        size_t tag_location = citations[i].find("url", 0);
        if (tag_location!=string::npos) {
            size_t equal_location = citations[i].find("=",tag_location);
            size_t end_location = citations[i].find("|",equal_location+1);
            size_t end_location2 = citations[i].find("}}",equal_location+1);
            if (end_location2<end_location) {
                end_location = end_location2;
            }
            domain = citations[i].substr(equal_location+1,end_location-equal_location-1);
            parse_domain(domain);
        }
        if (domain!="") {
            vector<string>::iterator it;
            it = find(cited_domains.begin(),cited_domains.end(),domain);
            if (it==cited_domains.end()) {
                cited_domains.push_back(domain);
            }
        }
    }
}

void parse_domain(string &domain) {
    domain = trim(domain);
    string http_junk = "://";
    size_t http_junk_location = domain.find(http_junk);
    if (http_junk_location!=string::npos) {
        domain = domain.substr(http_junk_location+http_junk.size());
    }
    size_t first_slash_location = domain.find("/");
    if (first_slash_location!=string::npos) {
        domain = domain.substr(0,first_slash_location);
    }
    while (count_string(domain,".")>3) {
        domain = domain.substr(domain.find(".")+1);
    }
}

void wikitext::read_cited_authors(vector<string> &citations) {
    for (int i=0; i<citations.size(); i++) {
        string author;
        size_t tag_location = citations[i].find("author=");
        if (tag_location==string::npos) {
            tag_location = citations[i].find("author =");
        }
        if (tag_location!=string::npos) {
            size_t equal_location = citations[i].find("=",tag_location);
            size_t end_location = citations[i].find("|",equal_location+1);
            size_t end_location2 = citations[i].find("}}",equal_location+1);
            if (end_location2<end_location) {
                end_location = end_location2;
            }
            author = citations[i].substr(equal_location+1,end_location-equal_location-1);
            parse_author(author);
        }
        else {
            size_t first_name_location = citations[i].find("first=");
            size_t last_name_location = citations[i].find("last=");
            if (first_name_location==string::npos) {
                first_name_location = citations[i].find("first =");
            }
            if (last_name_location==string::npos) {
                last_name_location = citations[i].find("last =");
            }
            // need to parse out the first and last names
            if (first_name_location!=string::npos and last_name_location!=string::npos) {
                size_t equal_location = citations[i].find("=",first_name_location);
                size_t end_location = citations[i].find("|",equal_location+1);
                size_t end_location2 = citations[i].find("}}",equal_location+1);
                if (end_location2<end_location) {
                    end_location = end_location2;
                }
                string first_name = citations[i].substr(equal_location+1,end_location-equal_location-1);
                first_name = trim(first_name);
                equal_location = citations[i].find("=",last_name_location);
                end_location = citations[i].find("|",equal_location+1);
                end_location2 = citations[i].find("}}",equal_location+1);
                if (end_location2<end_location) {
                    end_location = end_location2;
                }
                string last_name = citations[i].substr(equal_location+1,end_location-equal_location-1);
                last_name = trim(last_name);
                author = first_name+" "+last_name;
                parse_author(author);
            }
        }
        if (author!="") {
            vector<string>::iterator it;
            it = find(cited_authors.begin(),cited_authors.end(),author);
            if (it==cited_authors.end()) {
                cited_authors.push_back(author);
            } 
        }
    }
}

void parse_author(string &author) {

    decode_text(author);
    
    // if someone tried to put multiple authors in, keep only the first
    if ((author.find("&")!=string::npos)) {
        author = author.substr(0,author.find("&"));
    }
    
    // if someone tried to put multiple authors in, keep only the first
    if ((author.find(";")!=string::npos)) {
        author = author.substr(0,author.find(";"));
    }
    
    // if someone tried to put multiple authors in, keep only the first
    if ((author.find("and")!=string::npos)) {
        author = author.substr(0,author.find("and"));
    }
    
    // if someone put "By" in front of the name
    if ((author.find("By ")!=string::npos)) {
        author = author.substr(author.find("By ")+3);
    }

    // if the authors name is listed like "last, first"
    size_t comma_location = author.find(",");
    if (comma_location!=string::npos) {
        string first_name = author.substr(comma_location+1);
        string last_name  = author.substr(0,comma_location);
        first_name = trim(first_name);
        last_name  = trim(last_name);

        author = first_name+" "+last_name;
    }
    author = trim(author);
}

// removes various wikitext and xml
void wikitext::read_text(string &text){

    decode_text(text);
    remove_templates(text);

    // remove all category headers
    string target = "[[Category:";
    string endtarget = "]]";
    remove_between(text, target, endtarget);

    // remove all embedded urls
    target = "[http://";
    endtarget = "]";
    remove_between(text,target,endtarget);

    // remove all content between [[File: ]]
    remove_file_references(text);

    // remove all content between [[Image: ]] tags
    remove_image_references(text);

    target = "{|";
    endtarget = "}";
    remove_between(text,target,endtarget);

    target = "<!--";
    endtarget = "-->";
    remove_between(text,target,endtarget);

    remove_html(text);

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

    // Remove all escape chars
    remove_target(text,"\\");

    // Remove all \t
    remove_target(text,"\t");

    this->text = trim(text);
}

void remove_templates(string &text) {
    // remove all double bracket regions
    string open     = "{{";
    string close    = "}}";
    while (true) {
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
void remove_file_references(string &text) {

    string first = "[[File:";
    string begin = "[[";
    string end = "]]";

    size_t loc = 0;

    while (true) {
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
void remove_image_references(string &text) {

    string first = "[[Image:";
    string begin = "[[";
    string end = "]]";

    size_t loc = 0;

    while (true) {
        loc = text.find(first,loc);

        if (loc==string::npos) {
            return;
        }

        int openct = 1;
        int ct = 0;

        remove_nested(begin,end,text,loc,loc,openct,ct);
        if (ct >= 300) {
            return;
        }
    }
}

void decode_text(string &text) {
    replace_target(text, "&lt;", "<");
    replace_target(text, "&gt;", ">");
    replace_target(text, "&nbsp;", " ");
    replace_target(text, "&amp;", "&");
    replace_target(text, "&quot;", "\"");
    replace_target(text, "&apos;", "'");
}

void remove_references(string &temp){
    size_t ref = temp.find('*');
    if(ref!=string::npos){
        temp.erase(ref);
    }
}

void remove_html(string &text) {
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

    target = "<small";
    endtargets = {"/small>","/>"};
    remove_between(text,target,endtargets);

    target = "<code";
    endtargets = {"/code>","/>"};
    remove_between(text,target,endtargets);

    target = "<big";
    endtargets = {"/big>","/>"};
    remove_between(text,target,endtargets);

    target = "<source";
    endtargets = {"/source>","/>"};
    remove_between(text,target,endtargets);

}
