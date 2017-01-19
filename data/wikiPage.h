#ifndef WIKIPAGE_H
#define WIKIPAGE_H

using namespace std;

#include <string>
#include <vector>
#include <fstream>
#include <time.h>
#include <unistd.h>
#include <limits>
#include <stdio.h>
#include <sys/stat.h>
#include <algorithm>
#include <iostream>
#include "helpers.h"


class wikiPage {
public:
	string         title;        // Page title
	string         ns;           // Page namespace
	string         text;         // Page wikimarkup
	vector<string> categories;   // Page categories
	bool           isRedirect;   // Page redirect status
	string 		   redirection;	 // Redirection location
	int            quality;      // 0=Redirect, 1=Regular, 2=Good, 3=Bad
	string         contrib;      // Revision contributor
	string         timestamp;    // Revision timestamp
	short          pic;          // Total picture count
	string         templates;	 // Cleanup template (if any)
	short		   version;		 // Saved version
    vector<string>  template_vec;
    bool            isJunk;
    string          classification;
    unsigned long   size;
    string          save_location;
    string          temp; // for message passing

    // false if the page is not an article, i.e. it could have a title like
    // "Category:XXX" or could be a talk page
    bool            is_article;

	wikiPage(ifstream &wikiFile);// reload from file
	wikiPage(string pagestr, bool leave_wikitext, string code, vector<string> targs); // from string (choose formatting)
	void save(ofstream &file);
	void saveHTML(ofstream &file);
	void removeFormatting();
	friend ostream& operator<<(ostream& os, wikiPage& wp);
};

// wikipage constructor, leave_wikitext=false then remove formatting
wikiPage::wikiPage(string pagestr, bool leave_wikitext=false, string code="multi_strict",vector<string> targs={"null"}) 
{
    is_article = true; // set to true by default

    // only save if the article contains is in one of the requested categories
    if(code=="categories")
    {
        parse(pagestr,"[[Category:", "]]", categories);
        fix_cat(categories);
        //checking if I have any of the categories
        temp = "*none*";

        // check if the article fits into one of the provided categories
        for(int i=0; i<categories.size(); i++)
        {
            string cur = categories[i];
            cur = to_lowercase(cur);

            for(int k=0; k<targs.size(); k++)
            {
                if (cur == targs[k])
                {
                    temp = cur;
                    break;
                }
            }

            if (temp!="*none*")
            {
                break;
            }
        }

        // if this article fits into one of the designated categories
        if (temp!="*none*")
        {
            title = parse(pagestr, "<title>", "</title>"); // get the title

            // if the article is a category page, mark it
            if (title.find("Category:")!=string::npos)
            {
                is_article = false;
                return;
            }

            text = get_article_body(pagestr);
            if (text=="")
            {
                // page is junk so mark it and return from constructor
                isJunk = true;
                return;
            }
            isRedirect = false;
            if(isWithin(text, "#REDIRECT"))
                isRedirect = true;
            isJunk = false;
            size = sizeof(pagestr);
            removeFormatting();
            if (text=="")
            {
                // page is junk so mark it and return from constructor
                isJunk = true;
                return;
            }
            rebase_periods(text);
            return;
        }
    }

    // only parsing out the title and the article body and categories
    if(code=="category")
    {
        title = parse(pagestr, "<title>", "</title>");
        parse(pagestr, "[[Category:", "]]", categories);
        fix_cat(categories);
        return;
    }

    // only parsing out the article titles and categories
    if(code=="meta")
    {
        title = parse(pagestr, "<title>", "</title>");
        parse(pagestr, "[[Category:", "]]", categories);
        fix_cat(categories);
        return;
    }

	// RECOMMENDED, removes the most wikitext (almost perfect)
    if(code=="multi_strict")
    {
        title = parse(pagestr, "<title>", "</title>");
        contrib = parse(pagestr, "<username>", "</username>");
        timestamp = parse(pagestr, "<timestamp>", "</timestamp>");
        ns = parse(pagestr, "<ns>", "</ns>");
        parse(pagestr, "[[Category:", "]]", categories);
        fix_cat(categories);
        text = get_article_body(pagestr);
        if (text=="")
        {
            // page is junk so mark it and return from constructor
            isJunk = true;
            return;
        }
        classification = get_class(pagestr);
        isRedirect = false;
        if(isWithin(text, "#REDIRECT"))
            isRedirect = true;
        isJunk = false;
        size = sizeof(pagestr);
        removeFormatting();
        if (text=="")
        {
            // page is junk so mark it and return from constructor
            isJunk = true;
            return;
        }
        rebase_periods(text);
        return;
    }
    if(code=="title")
    {
        title = parse(pagestr, "<title>", "</title>");
        text = get_article_body(pagestr);
        isJunk = false;
        removeFormatting();
        isRedirect = false;
        if(isWithin(text, "#REDIRECT"))
            isRedirect = true;
        return;
    }
}

// removes various wikitext and xml
void wikiPage::removeFormatting(){

    string temp = text;

    // remove all double bracket regions
    bool condition  = true;
    string open     = "{{";
    string close    = "}}";
    while(condition){
        size_t location = temp.find(open);
        if(location!=string::npos){
            int openCt  = 1;
            int ct      = 0;
            nestedRemoval(open, close, temp, location, location, openCt, ct);

            if (temp=="")
            {
                isJunk = true; // there was an error
                text = temp; // let the constructor know there was an error
                return;

            }
            if(ct>=300)
            {
                condition=false;
                isJunk = true; //There was an error
                return;        //So not going to save this article
            }
        }
        else{
            condition=false;
        }
    }

    // remove all category headers
    string target = "[[Category:";
    string endtarget = "]]";
    removeBetween(temp, target, endtarget);

    // remove all content between [[File: ]]
    remove_file_references(temp);

    // remove all content between [[Image: ]] tags
    remove_image_references(temp);

    // remove region within triple periods: ...[[this is a |... test]]
    target = "[[";
    endtarget = "|";
    r_removeBetween(temp, target, endtarget);

    // remove all ]]
    target = "]]";
    removeTarget(temp, target);

    // remove all [[
    target = "[[";
    removeTarget(temp, target);

    // remove all '''
    target = "'''";
    removeTarget(temp, target);


    target = "&lt;ref";
    vector<string> endtargets = {"/ref&gt;","/&gt;"};
    removeBetween(temp,target,endtargets);

    target = "&lt;references";
    endtargets = {"/references&gt;","/ref&gt;","/&gt;"};
    removeBetween(temp,target,endtargets);

    target = "&lt;nowiki";
    endtargets = {"/nowiki&gt;","/&gt;"};
    removeBetween(temp,target,endtargets);

    target = "&lt;!--";
    endtargets = {"--&gt;","&gt;"};
    removeBetween(temp,target,endtargets);

    target = "&lt;math";
    endtargets = {"/math&gt;","/&gt;"};
    removeBetween(temp,target,endtargets);

    target = "&lt;gallery";
    endtargets = {"/gallery&gt;","/&gt;"};
    removeBetween(temp,target,endtargets);

    target = "&lt;hiddentext";
    endtargets = {"/hiddentext&gt;","/&gt;"};
	removeBetween(temp,target,endtargets);    

    target = "==";
    endtarget = "==";
    removeBetween(temp, target, endtarget);

    target = "===";
    endtarget = "===";
    removeBetween(temp, target, endtarget);

    target = "ref&gt;";
    replaceTarget(temp,target," ");

    replaceTarget(temp, {"     ","    ","  "}, " ");
    removeTarget(temp, "&quot;");
    removeTarget(temp, "''");
    removeTarget(temp, "&amp;");
    removeTarget(temp, "nbsp;");
    vector<string> vec{"...",".."};
    replaceTarget(temp, vec, ".");
    replaceTarget(temp, "=", " ");
    removeReferences(temp);
    removeTarget(temp,"#");
    removeTarget(temp, "&gt");
    removeBetween(temp, "(;", ")");
    removeBetween(temp, "{|", "}");
    removeBetween(temp, "<ref name", ";", "strict");
    removeTarget(temp, "—");
    removeTarget(temp, "()");
    replaceTarget(temp, ".", ". ", "strict");
    replaceTarget(temp, ".   ", ".  ", "string");
    removeTarget(temp,"&lt;sub;"); // remove subscript opener 
    removeTarget(temp,"&lt;/sub;"); // remove subscript closer
    removeTarget(temp,"&lt;sup;"); // remove superscript opener
    removeTarget(temp,"&lt;/sup;"); // remove superscript closer
    removeTarget(temp,"&lt;blockquote;"); // remove b--lockquote opener
    removeTarget(temp,"&lt;/blockquote;"); // remove blockquote closer
    removeTarget(temp,"&lt;references;"); // remove references opener
    removeTarget(temp,"&lt;/references;"); // remove references closer
    //removeTarget(text,"&lt;gallery;"); // remove gallery operer
    removeTarget(text,"&lt;/gallery;"); // remove gallery closer
    text = temp;
    return;
}

// reads in a wikipage from file
wikiPage::wikiPage(ifstream &wikiFile){
	string versionOneTag = "---> VERSION 1.0";
	string buffer;
	getline(wikiFile, buffer);
	if(buffer.find(versionOneTag)!=string::npos){
		version=1;
		getFileHeaderTitle(wikiFile, title);
		getFileHeader(wikiFile, ns);
		getline(wikiFile, buffer);
		getFileHeader(wikiFile, isRedirect);
		getFileHeader(wikiFile, redirection);
		getFileHeader(wikiFile, quality);
		getFileHeader(wikiFile, contrib);
		getFileHeader(wikiFile, timestamp);
		getFileHeader(wikiFile, pic);
		getFileHeader(wikiFile, templates);
		while(true){
			getline(wikiFile, buffer);
			text+=buffer;
			if(wikiFile.eof()){
				break;
			}
		}
	}
	else{
		cout<<"Save version not recognized!\n";
		return;
	}
}

//Save function (save to file)
void wikiPage::save(ofstream &file){

	file<<"---> VERSION 1.0\n";
	file<<(*this);
	file<<"Categories:\t";
	for(int i=0; i<categories.size(); i++){
		file<<"["<<categories[i]<<"] ";
	}
	file<<"\n\n"<<text<<"\n";
	file<<"---> EOA\n";
}

//Save to HTML format of website
void wikiPage::saveHTML(ofstream &file){
	file<<"<!DOCTYPE html>\n";
	file<<"<html>\n";
	file<<"\t<head>\n";
	file<<"\t\t<link rel=\"stylesheet\" href=\"../styles/main.css\">\n";
	file<<"\t\t<title>"<<title<<"</title>\n";
	file<<"\t\t<script>\n";
	file<<"\t\t\tfunction colorText() {\n";
	file<<"\t\t\t\tvar p = document.getElementsByClassName('text')\";\n";
	file<<"\t\t\t\tvar colors = [\"#FFD700\",\"#FFD700\",\"#CCC\", \"#CCC\"]\";\n";
	file<<"\t\t\t\tfor(var i=0) \"; i < p.length\"; i++){\n";
	file<<"\t\t\t\t\tp[i].style.background = colors[i];\n";
	file<<"\t\t\t\t}\n";
	file<<"\t\t\t}\n";
	file<<"\t\t</script>\n";
	file<<"\t</head>\n";
	file<<"\t<body onload=\"colorText()\">\n";
	file<<"\t\t<div id=\"header\">\n";
	file<<"\t\t\t<a href=\"../index.html\">\n";
	file<<"\t\t\t\t<img id=\"logo\" class=\"center\" src=\"../images/logo.svg\" alt=\"WikiClassify\" width=\"250px\"/>\n";
	file<<"\t\t\t</a>\n";
	file<<"\t\t\t<input type=\"text\" name=\"search\" placeholder=\"Search\" id=\"search\" class=\"center\" >\n";
	file<<"\t\t</div>\n";
	file<<"\t\t<div id=\"content\" class=\"center box\">\n";
	file<<"\t\t\t<h1>"<<title<<"</h1>\n";

	if(quality==2){file<<"\t\t\t<span class=\"label featured\">Featured</span>\n";}
	if(quality==1){file<<"\t\t\t<span class=\"label stub\">Stub</span>\n";}

	file<<"\t\t\t<p>\n";

	string period = ".";
	size_t front = 0;
	size_t back=0;
	string temp;
	while(true){
		back = text.find(period, front);
		if(back!=string::npos){
			temp = text.substr(front,back-front);
			file<<"\t\t\t\t<span class='text'>"<<temp<<"</span>\n";
			front = back+2;
		}
		else{
			break;
		}
	}

	file<<"\t\t\t</p>\n";
	file<<"\t\t</div>\n";
	file<<"\t\t\t<nav>\n";
	file<<"\t\t\t\t<a href=\"../about.html\">About</a>\n";
	file<<"\t\t\t\t<a href=\"../login.html\">Login</a>\n";
	file<<"\t\t\t</nav>\n";
	file<<"\t\t</div>\n";
	file<<"\t</body>\n";
	file<<"</html>\n";
}

// default output operator
ostream& operator<<(ostream& os, wikiPage& wp){
    os <<"Title:\t\t"<<wp.title<<"\nNamespace:\t"<<wp.ns<<"\nSize:\t\t"<<wp.text.size()<<"\nRedirect:\t"<<wp.isRedirect<<"\nRedir_loc:\t"<<wp.redirection<<"\nQuality:\t"<<wp.quality<<"\nContrib.:\t"<<wp.contrib<<"\nTimestamp:\t"<<wp.timestamp<<"\nPic Count:\t"<<wp.pic<<"\nTemplate:\t"<<wp.templates<<"\n";
    return os;
}

#endif // WIKIPAGE_H