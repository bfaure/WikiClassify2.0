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