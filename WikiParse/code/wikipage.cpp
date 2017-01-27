#include "wikipage.h"
#include "string_utils.h"
#include "wikitext.h"

wikipage::wikipage(string page) {
    get_namespace(page);             // Extract page sections
    if (is_article()) {
        get_ID(page);
        get_title(page); 
        get_redirect(page);
        if (!is_redirect()) {
            get_timestamp(page); 
            //get_contributor(page);
            //get_comment(page);
            get_text(page);         
            if (!is_disambig()) {   // if not a disambugation tagged article

                read_categories();  // get list of category strings
                read_citations();  // get list of citation structs
                flatten_citations(); // flatten citations if they have the same url and author
                
                get_daily_views();
                get_quality();
                get_importance();
                get_instance(); 

                //read_links();       
                //read_image_count();
                clean_text();       // remove all formatting from text
            }
        }
    }
}

void wikipage::flatten_citations()
{
    // iterates over all citations in a wikipage and if any contain the same elements (i.e. if two 
    // citations share an author or a url) the elements that are the same are set to "None" in 
    // one of the citations. This prevents the save_json function from outputting copies of the same 
    // information if a source or author is used multiple times in an article.
    if (citations.size()>1)
    {
        int i = 0;
        while (true)
        {
            if (i>citations.size()-1)
            {
                return;
            }

            string cur_url = citations[i].get_url();
            string cur_author = citations[i].get_author();

            if (cur_url=="None" and cur_author=="None")
            {
                i++;
                continue;
            }

            for (int j=0; j<citations.size(); j++)
            {
                if (j!=i)
                {
                    if(citations[j].get_url()==cur_url)
                    {
                        citations[i].remove_url();
                    }
                    if(citations[j].get_author()==cur_author)
                    {
                        citations[i].remove_author();
                    }
                }
            }
            i++;
        }
    }
}

void wikipage::get_instance()
{
    instance = ""; // default
}

void wikipage::get_quality()
{
    if (text.find("{{featured article}}")!=string::npos)
    {
        quality = "featured";
        return;
    }
    if (text.find("{{good article}}")!=string::npos)
    {
        quality = "good";
        return;
    }
    if (text.find("{{stub}}")!=string::npos)
    {
        quality = "stub";
        return;
    }
    quality = "";
}

void wikipage::get_importance()
{
    importance = ""; //default
}

void wikipage::get_daily_views()
{
    daily_views = ""; // default
}

void wikipage::read_citations()
{
    /* reads through article body (pre-clean_text()) and gathers together all of the embedded citations used */
    // because this happens before the article body is decoded, we need to use the &lt and &gt codes
    vector<string> parsed_citation_strings;
    //vector<citation> citations;

    string target = "{{cite";
    string endtarget = "}}";
    copy_between(text,target,endtarget,parsed_citation_strings);
    //cout<<"Found "+to_string(parsed_citation_strings.size())+" citations in "+title+"\n";

    target = "{{Citation";
    copy_between(text,target,endtarget,parsed_citation_strings);

    string last = "";
    for (int i=0; i<parsed_citation_strings.size(); i++)
    {
        if (parsed_citation_strings[i] == last)
        {
            //cout<<"copy: "<<parsed_citation_strings[i]<<"\n";
            continue; // skip citations that are the same
        }
        // iterate over all parsed references and construct citation structs
        if (parsed_citation_strings[i] != "")
        {
            citation cur(parsed_citation_strings[i]); // populate citation struct
            citations.push_back(cur);  
        }
        last = parsed_citation_strings[i];
    }
    //return citations;
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

bool first_save = true; // dont write out the pre-comma for the first article

void wikipage::save_json(ofstream &file)
{
    // outputs in json format on a single line of the file
    if(!text.empty())
    {
        if(is_disambig())
        {
            return;
        }

        string divider = "";
        if (first_save==false) { divider = ",\n"; }
        if (first_save==true) { first_save = false; }
        string output = divider;

        output += "\""+to_string(ID)+"\":{";                // {id:{
        output += "\"title\":\""+title+"\",";              // title:"Article title",
        output += "\"ns\":\""+ns+"\",";                         // ns:Article namespace,
        output += "\"timestamp\":\""+timestamp+"\",";           // timestamp:Article timestamp,    
        output += "\"instance_of\":\""+instance+"\",";   // instance_of:"Article instance_of",
        output += "\"quality\":\""+quality+"\",";
        output += "\"importance\":\""+importance+"\",";
        output += "\"daily_views\":\""+daily_views+"\",";
        output += "\"text\":\""+text+"\",";
        output += "\"categories\":[";
        for (int i=0; i<categories.size(); i++)
        {
            output += "\""+categories[i]+"\"";
            if (i!=categories.size()-1)
            {
                output += ",";
            }
        }
        output += "],";
        output += "\"cited_domains\":[";
        for (int i=0; i<citations.size(); i++)
        {
            string cur = citations[i].get_url();
            if (cur==" " or cur=="" or cur=="None") // if the current url is empty
            {
                if (i==citations.size()-1) // if this is the last iteration
                {
                    if (output.at(output.size()-1)==',')
                    {
                        output.erase(output.size()-1); // erase the extra comma
                    }
                }
                continue;
            }

            output += "\""+cur+"\"";
            if (i!=citations.size()-1)
            {
                output += ",";
            }
        }
        output += "],";
        output += "\"cited_authors\":[";
        for (int i=0; i<citations.size(); i++)
        {
            string cur = citations[i].get_author();
            if (cur==" " or cur=="" or cur=="None") // if the current author is empty
            {
                if (i==citations.size()-1) // if this is the last iteration
                {
                    if (output.at(output.size()-1)==',') // if there is an extra comma 
                    {
                        output.erase(output.size()-1); // erase the extra comma
                    }
                }
                continue;
            }
            output += "\""+cur+"\""; // add the current author to the output string
            if (i!=citations.size()-1) // if this is not the last iteration
            {
                output += ","; // add comma between author names
            }
        }
        output += "]";
        output += "}";
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

    target = "<small";
    endtargets = {"/small>","/>"};
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


string get_base_url(string url)
{
    // takes in a full url and returns just the base, i.e. it removes the stuff
    // before the domain name and the stuff after the .com, .org, etc.

    string http_junk = "://";
    size_t http_junk_location = url.find(http_junk);

    if (http_junk_location!=string::npos)
    {
        url = url.substr(http_junk_location+http_junk.size());
    }
    vector<string> exts = {".com",".edu",".org",".gov",".mil",".net",".info",".ca",".int",".biz",".name",".br",".cn",".fr",".co.uk",".am",".ar"};
    for (int i=0; i<exts.size(); i++)
    {
        size_t ext_location = url.find(exts[i]);
        if (ext_location!=string::npos)
        {
            url = url.substr(0,ext_location+exts[i].size());
            return url;
        }
    }
    return url;
}

string citation::get_url()
{
    return base_url;
}

string citation::get_author()
{
    return author;
}

void citation::remove_url()
{
    base_url = "None";
    url = "None";
}

void citation::remove_author()
{
    author = "None";
}


void citation::read_url(const string &src)
{
    url = "None";
    size_t tag_location = src.find("url");
    if (tag_location!=string::npos)
    {
        // find location of first equal sign after the "url" tag
        size_t equal_location = src.find("=",tag_location);

        size_t end_location = src.find("|",equal_location+1);
        size_t end_location2 = src.find("}}",equal_location+1);

        if(end_location2<end_location)
        {
            end_location = end_location2;
        }

        url = src.substr(equal_location+1,end_location-equal_location-1);
        url = trim(url);

        base_url = get_base_url(url);
        return;
    }
}

void citation::read_author(const string &src)
{
    author = "None";
    size_t tag_location = src.find("author");
    if (tag_location != string::npos)
    {
        // find location of first equals sign after the "author" tag
        size_t equal_location = src.find("=",tag_location);

        size_t end_location = src.find("|",equal_location+1);
        size_t end_location2 = src.find("}}",equal_location+1);

        if(end_location2<end_location)
        {
            end_location = end_location2;
        }

        author = src.substr(equal_location+1,end_location-equal_location-1);
        author = trim(author);

        if (author.find(",")!=string::npos)
        {
            // if the authors name is listed like "last, first"
            //cout<<"Fixing this author name: "<<author;
            string last = author.substr(0,author.find(","));
            string first = author.substr(author.find(",")+1);
            if (first=="" or first==" ")
            {
                author = trim(last);
            }
            else
            {
                if (last=="" or last==" ")
                {
                    author = trim(first);
                }
                else
                {
                    author = trim(first)+" "+trim(last);
                }
            }
            //cout<<", fixed to "<<author<<"\n";
        }
        return;
    }

    // if we get here then the citation is not using the "author=" tag, rather, 
    // they may be using "first=" and "last=" or they may not be including an author
    size_t first_name_location = src.find("first");
    size_t last_name_location = src.find("last");
    if(first_name_location!=string::npos and last_name_location!=string::npos)
    {
        // need to parse out the first and last names
        // for the first name
        size_t equal_location = src.find("=",first_name_location);

        size_t end_location = src.find("|",equal_location+1);
        size_t end_location2 = src.find("}}",equal_location+1);

        if(end_location2<end_location)
        {
            end_location = end_location2;
        }

        string first_name = src.substr(equal_location+1,end_location-equal_location-1);
        first_name = trim(first_name);

        // need to parse out the first and last names
        // for the first name
        equal_location = src.find("=",last_name_location);

        end_location = src.find("|",equal_location+1);
        end_location2 = src.find("}}",equal_location+1);

        if(end_location2<end_location)
        {
            end_location = end_location2;
        }

        string last_name = src.substr(equal_location+1,end_location-equal_location-1);
        last_name = trim(last_name);

        author = first_name+" "+last_name;
        return;
    }
    //cout<<"Could not find author for "+title+"\n";
}

void check_escape_chars(string &src)
{
    if (src.find("\\"))
    {
        cout<<"Found escape character in this string: "<<src<<"\n";
    }

}

citation::citation(const string &src)
{
    // citation default constructor
    read_url(src);
    read_author(src);

    remove_target(author,"\n");
    remove_target(base_url,"\n");

    remove_target(author,"\t");
    remove_target(base_url,"\t");

    remove_target(author,"\"");
    remove_target(base_url,"\"");

    //check_escape_chars(author);
    //check_escape_chars(base_url);

    //string temp = src;
    //remove_target(temp,"\n");

    //cout<<"CITATION SUMMARY, TOOK IN: "<<temp<<" AND GOT THIS AUTHOR: "<<author<<" AND THIS URL: "<<base_url<<"\n\n";
}