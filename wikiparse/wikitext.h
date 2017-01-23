#ifndef WIKITEXT_H
#define WIKITEXT_H

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
#include <ctype.h>

void remove_target(string &temp, string target);
void remove_target(string &temp, string target);
void remove_references(string &temp);
void remove_between(string &temp, string target, vector<string> endtargets);
void remove_between(string &temp, string target, string endtarget, string code);
void remove_between(string &temp, string target, string endtarget);
void remove_between_r(string &temp, string target, string endtarget);
void remove_nested(string begintarg, string endtarg, string &text, size_t &current, size_t begin, int &openCt, int &ct);
void replace_target(string &temp, string target, string new_target, string code);
void replace_target(string &temp, string target, string new_target);
void replace_target(string &temp, vector<string> target, string new_target);
void replace_target(string &temp, string target, string new_target);

// finds any instances of target and clips until it finds the closest endtarget
void remove_between(string &temp, string target, vector<string> endtargets){
    while(true){
        size_t location = temp.find(target);
        if(location!=string::npos){

        	int closest_partner = 1000000000;
        	int close_cut_at = -1;

        	for (int i=0; i<endtargets.size(); i++){

        		string endtarget = endtargets[i];
	            size_t endlocation = temp.find(endtarget, location+target.size());

	            if(endlocation!=string::npos){

	            	if (close_cut_at==-1){
	            		close_cut_at = endlocation+endtarget.size()-location;
	            		closest_partner = endlocation;
	            	}

	            	else{

	            		if (endlocation < closest_partner){
	            			close_cut_at = endlocation+endtarget.size()-location;
	            			closest_partner = endlocation;
	            		}
	            	}
	            }
	        }

	        if (close_cut_at==-1){
	        	return;
	        }

	        temp.erase(location, close_cut_at);

        }

        else{
            return;
        }
    }
}

void remove_target(string &temp, string target);

void replace_target(string &temp, string target, string new_target);

void remove_between(string &temp, string target, string endtarget, string code){
    while(true){
        size_t location = temp.find(target);
        if(location!=string::npos){
            size_t endlocation = temp.find(endtarget, location+target.size());
            if((endlocation!=string::npos) && ((endlocation - location) < 50)){
                temp.erase(location, endlocation+endtarget.size()-location);
            }
            else{
                return;
            }
        }
        else{
            return;
        }
    }
}

void replace_target(string &temp, string target, string new_target, string code){
    size_t loc = 0;
    while(true){
        size_t location = temp.find(target, loc);
        if(location!=string::npos){
            temp.replace(location, target.size(), new_target);
            loc = location + new_target.size();
        }
        else{
            return;
        }
    }
}

//Both begintarg & endtarg must be same length for function to work
void remove_nested(string begintarg, string endtarg, string &text, size_t &current, size_t begin, int &openCt, int &ct){
    ct++;
    if(ct >= 300){
    	cout<<"\r                                                                                      ";
        cout<<"\rError in remove_nested(), trying to snip between "<<begintarg<<" and "<<endtarg<<".\n";
        cout.flush();
        text = "";
        return;
    }
    if(openCt<=0){
        text.erase(begin, current+endtarg.size()-begin);
        return;
    }
    size_t closeLocation = text.find(endtarg, current+begintarg.size());
    if(closeLocation==string::npos){
        text.erase(begin, string::npos);
        return;
    }
    size_t temp = current;
    while(true){
        size_t nests = text.find(begintarg, temp+begintarg.size());
        if((nests>closeLocation) || (nests==string::npos)){
            break;
        }
        else{
            openCt++;
            temp = nests;
        }
    }
    openCt--;
    return remove_nested(begintarg, endtarg, text, closeLocation, begin, openCt, ct);
}

void remove_between(string &temp, string target, string endtarget){
    while(true){
        size_t location = temp.find(target);
        if(location!=string::npos){
            size_t endlocation = temp.find(endtarget, location+target.size());
            if(endlocation!=string::npos){
                temp.erase(location, endlocation+endtarget.size()-location);
            }
            else{
                return;
            }
        }
        else{
            return;
        }
    }
}

//reverse removeBetween
void remove_between_r(string &temp, string target, string endtarget){
    while(true){
        size_t location = temp.rfind(endtarget);
        if(location!=string::npos){
            size_t endlocation = temp.rfind(target, location-target.size());
            if(endlocation!=string::npos){
                temp.erase(endlocation, location+endtarget.size()-endlocation);
            }
            else{
                return;
            }
        }
        else{
            return;
        }
    }
}

void remove_target(string &temp, string target){
    while(true){
        size_t location = temp.find(target);
        if(location!=string::npos){
            temp.erase(location,target.size());
        }
        else{
            return;
        }
    }
}

void replace_target(string &temp, string target, string new_target){
    while(true){
        size_t location = temp.find(target);
        if(location!=string::npos){
            temp.replace(location, target.size(), new_target);
        }
        else{
            return;
        }
    }
}

void replace_target(string &temp, vector<string> target, string new_target){
    for(int i=0; i<target.size(); i++){
        string targ = target[i];
        bool condition=true;
        while(condition){
            size_t location = temp.find(targ);
            if(location!=string::npos){
                temp.replace(location, targ.size(), new_target);
            }
            else{
                condition=false;
            }
        }
    }
}

void remove_references(string &temp){
    size_t ref = temp.find('*');
    if(ref!=string::npos){
        temp.erase(ref);
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

#endif // WIKITEXT_H