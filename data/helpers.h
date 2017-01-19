#ifndef HELPERS_H
#define HELPERS_H

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

void 	rebase_periods(string &page);
void 	removeBetween(string &temp, string target, vector<string> endtargets);
void 	remove_file_references(string &page);
void 	remove_image_references(string &page);
void 	getPage(ifstream &dataDump, bool &end, string &pagestr);
string 	get_article_body(string str);
string 	get_class(string input);
void 	removeTarget(string &temp, string target);
void 	fix_cat(vector<string> &cat);
void 	replaceTarget(string &temp, string target, string new_target);
void 	fix_title(string &title);

void 	removeBetween(string &temp, string target, string endtarget, string code);
void 	replaceTarget(string &temp, string target, string new_target, string code);
void 	nestedRemoval(string begintarg, string endtarg, string &text, size_t &current, size_t begin, int &openCt, int &ct);
void 	removeBetween(string &temp, string target, string endtarget);
void 	r_removeBetween(string &temp, string target, string endtarget);
void 	removeTarget(string &temp, string target);
void 	replaceTarget(string &temp, string target, string new_target);
void 	replaceTarget(string &temp, vector<string> target, string new_target);
void 	removeReferences(string &temp);

string 	get_path();
void 	create_directory(string directory);
void 	remove_directory(string directory);
void 	create_readme(string parent, string code);
void 	create_readme(string parent);
bool 	isWithin(string &str, string tag1);
string 	parse(string &str, string tag1, string tag2);
int 	parse(string &str, string tag1, string tag2, vector<string> &result);
short 	picCount(string &article);
bool 	getTemplates(string &input, string &temp);
string 	getRedirect(string &input);

void 	getFileHeaderTitle(ifstream &wikiFile, string &subject);
void 	getFileHeader(ifstream &wikiFile, string &subject);
void 	getFileHeader(ifstream &wikiFile, int &subject);
void 	getFileHeader(ifstream &wikiFile, short &subject);
void 	getFileHeader(ifstream &wikiFile, bool &subject);


// convert a string to lowercase
string to_lowercase(string &input)
{
	std::transform(input.begin(),input.end(),input.begin(),::tolower);
	return input;

	int i=0;
	vector<char> str(input.c_str(), input.c_str()+input.size()+1);

	char c;
	while(str[i])
	{
		c = str[i];
		putchar(tolower(c));
		i++;
	}
	string temp(str.begin(),str.end());
	return temp;
}


vector<string> split(const string &cat_str, string delim);

// class used by category_handler
class category_metadata
{
public:
	string name;
	vector<string> articles;
	category_metadata()
	{
		name = "";
	}
	void save(string folder)
	{
		string filename = folder+"/"+name+".txt";
		ofstream file(filename);
		file<<"[Category: "+name+"]\n";
		for(int i=0; i<articles.size(); i++)
		{
			file<<"["<<articles[i]<<"]\n";
		}
	}
};

// class used by investigate_meta
class category_handler
{
public:
	vector<category_metadata> cats;
	int sift_rate;
	int insertion;
	int sift_threshold;
	int checkpoint;
	int last_checkpoint;
	int save_threshold;

	category_handler()
	{
		// after sift_rate insertions, all cats with less than
		// sift_threshold articles will be removed from the cats vector
		sift_rate = 20000;
		insertion = 0;
		sift_threshold = 10;
		save_threshold = 100;

		// save every checkpoint seconds as backup
		checkpoint = 1800; // every 30 minutes
		last_checkpoint = time(0);
	}

	// remove all cats with < sift_threshold articles
	void sift()
	{
		int i=0;
		while (true)
		{
			if (cats[i].articles.size() < sift_threshold)
			{
				cats.erase(cats.begin()+i);
			}
			else{
				i++;
			}
			if (i>=cats.size())
			{
				break;
			}
		}
	}

	// add the data for a single article, a single article comes with
	// a single title and possibly several categories
	void add_entry(string &article_title, string &article_cats)
	{
		insertion++;
		if (insertion >= sift_rate)
		{
			insertion = 0;
			sift();
		}

		if (time(0)-last_checkpoint>=checkpoint)
		{
			last_checkpoint = time(0);
			save_results(true);
		}

		vector<string> art_cats = split(article_cats, " | ");

		for (int k=0; k<art_cats.size(); k++)
		{
			bool found_match = false;

			for(int i=0; i<cats.size(); i++)
			{
				if (art_cats[k] == cats[i].name)
				{
					cats[i].articles.push_back(article_title);
					found_match = true;
					break;
				}
			}	

			if (!found_match)
			{
				category_metadata temp;
				temp.name = art_cats[k];
				temp.articles.push_back(article_title);
				cats.push_back(temp);
			}		
		}
	}

	void save_results(bool is_checkpoint = false)
	{
		if (!is_checkpoint)
		{
			cout<<"found "<<cats.size()<<" individual categories\n";
		}
		
		string parent_folder = "meta";
		string folder = parent_folder+"/test-"+to_string(time(0));
		create_directory("/"+folder);
		int num_saved = 0;
		long long total_articles = 0; 

		if (!is_checkpoint)
		{
			cout<<"using save_threshold = "<<save_threshold<<"\n";
			cout<<"writing details to "<<folder<<"...\n";
		}

		for (int i=0; i<cats.size(); i++)
		{
			total_articles += cats[i].articles.size();
			if (cats[i].articles.size() >= save_threshold)
			{
				num_saved++;
				cats[i].save(folder);
			}
		}

		if (is_checkpoint)
		{
			cout.flush();
			cout<<"\r                                           ";
			cout<<"\rfinished saving data [checkpoint].\n";
			cout.flush();			
		}

		if (!is_checkpoint)
		{
			cout<<"finished saving data.\n";
		}

		if (!is_checkpoint)
		{
			if (cats.size()!=0)
			{
				cout<<"average articles per category = "<<total_articles/cats.size()<<"\n";	
			}
			cout<<"number of categories saved = "<<num_saved<<"\n";
		}
	}
};


vector<string> split(const string &cat_str, string delim) {
    vector<string> elems;
    size_t loc = 0;
    size_t next_loc = 0;

    bool condition = true;
    while(condition)
    {
    	next_loc = cat_str.find(delim,loc);

    	if (next_loc != string::npos)
    	{
    		elems.push_back(cat_str.substr(loc,next_loc-loc));
    	}

    	if (next_loc==string::npos)
    	{
    		elems.push_back(cat_str.substr(loc,string::npos));
    		condition = false;
    		continue;
    	}

    	loc = next_loc+delim.size();
    }
    return elems;
}

// parses a readme file and returns all filenames, used by investigate_meta
vector<string> parse_lines(string filename)
{
	ifstream readme(filename);
	vector<string> filenames;

	while (readme)
	{
		string line;
		getline(readme,line);
		line.erase(remove(line.begin(),line.end(),'\n'),line.end());
		line.erase(remove(line.begin(),line.end(),'\r'),line.end());
		if (line != "")
		{
			filenames.push_back(line);	
		}
	}
	return filenames;
}

// places all sentence-end periods back (" . "-->". ")
void rebase_periods(string &page){

	while (true)
	{
		size_t loc = page.find(" . ");
		if (loc != string::npos){
			replaceTarget(page," . ",". ");
		}
		else{
			return;
		}
	}
}

// finds any instances of target and clips until it finds the closest endtarget
void removeBetween(string &temp, string target, vector<string> endtargets){
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

// nested type removal of [[File: ]]
void remove_file_references(string &page){

	string first = "[[File:";
	string begin = "[[";
	string end = "]]";

	size_t loc = 0;

	while (true)
	{
		loc = page.find(first,loc);

		if (loc==string::npos)
		{
			return;
		}

		int openct = 1;
		int ct = 0;

		nestedRemoval(begin,end,page,loc,loc,openct,ct);
		if (ct >= 300){
			return;
		}
	}
}

// nested type removal of [[Image: ]]
void remove_image_references(string &page){

	string first = "[[Image:";
	string begin = "[[";
	string end = "]]";

	size_t loc = 0;

	while (true)
	{
		loc = page.find(first,loc);

		if (loc==string::npos)
		{
			return;
		}

		int openct = 1;
		int ct = 0;

		nestedRemoval(begin,end,page,loc,loc,openct,ct);
		if (ct >= 300){
			return;
		}
	}
}

//Get a page from the data dump
void getPage(ifstream &dataDump, bool &end, string &pagestr){

	unsigned short buffersize = 4096;
	unsigned long blocksize = 1024000;
	string block;
	char buffer[buffersize];

	string line;
	bool condition=true;
	while(condition){
		getline(dataDump, line);
		if(line.find("<page>") != string::npos){
			while(true){
				getline(dataDump, line);
				if(line.find("</page>") != string::npos){
					return;
				}
				if (dataDump.eof()){
					end = true;
					return;
				}
				pagestr.append(line);
			}
		}
		if (dataDump.eof()){
			end = true;
			return;
		}
	}
}

string get_article_body(string str){
	string open_targ = "<text xml:space=\"preserve\"";
	string close_targ = "</text>";

	size_t p1 = str.find(open_targ);
	size_t p2 = str.find(">",p1+1);
	size_t p3 = str.find(close_targ,p2);

	if (p1!=string::npos and p2!=string::npos and p3!=string::npos){
		return str.substr(p2+1, p3-p2-1);
	}
	else{
		cout.flush();
		cout<<"\r                                                                    ";
		cout<<"\rError in get_article_body().\n";
		cout.flush();
		return "";
	}
}

string get_class(string input){
    vector<string> common = {"{{All plot", "{{Advert", "{{Buzzword", "{{Repetition",
                              "{{Tone|article", "{{Peacock", "{{Incomprehensible",
                              "{{Weasel", "{{Generalize", "{{Partisan", "{{Unbalanced",
                             "{{Featured article}}", "{{Good article}}", "#REDIRECT", "{{Stub", "stub}}"};

    vector<string> clean = {"plot", "advert", "buzzword", "repetition", "tone",
                            "peacock", "incomprehensible", "weasel",
                            "generalize", "partisan", "unbalanced", "featured",
                            "good", "redirect", "stub", "stub"};

    for(int i=0; i<common.size(); i++){
        if(isWithin(input, common[i])){
            return clean[i];
        }
    }
    return "other";
}

void removeTarget(string &temp, string target);

void fix_cat(vector<string> &cat){
    vector<string> temp;
    for(int i=0; i<cat.size(); i++){
        string str = cat[i];
        replaceTarget(str,"|"," --> ");
        //removeTarget(str, "|");
        temp.push_back(str);
    }
    cat = temp;
}

void replaceTarget(string &temp, string target, string new_target);

void fix_title(string &title){
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

void removeBetween(string &temp, string target, string endtarget, string code){
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

void replaceTarget(string &temp, string target, string new_target, string code){
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
void nestedRemoval(string begintarg, string endtarg, string &text, size_t &current, size_t begin, int &openCt, int &ct){
    ct++;
    if(ct >= 300){
    	cout<<"\r                                                                                      ";
        cout<<"\rError in nestedRemoval(), trying to snip between "<<begintarg<<" and "<<endtarg<<".\n";
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
    return nestedRemoval(begintarg, endtarg, text, closeLocation, begin, openCt, ct);
}

void removeBetween(string &temp, string target, string endtarget){
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
void r_removeBetween(string &temp, string target, string endtarget){
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

void removeTarget(string &temp, string target){
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

void replaceTarget(string &temp, string target, string new_target){
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

void replaceTarget(string &temp, vector<string> target, string new_target){
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

void removeReferences(string &temp){
    size_t ref = temp.find('*');
    if(ref!=string::npos){
        temp.erase(ref);
    }
}

//Get current directory
string get_path(){
	const int max_path_size = 500;
	char temp[max_path_size];
	getcwd(temp, max_path_size);
	string cwd(temp);
	return cwd;
}

//Make a directoy in current folder
void create_directory(string directory){
	char *p = new char[500];
	string path = get_path();
	string mkdir = "mkdir ";
	string quote = "\"";
	string command = mkdir+quote+path+directory+quote;
	char *c = const_cast<char*>(command.c_str());
	system(c);
	return;
}

//Create readme.txt files to hold info
void create_readme(string parent, string code){
	if(code=="one"){
		time_t _tm = time(NULL);
		struct tm* curtime = localtime(&_tm);
		string cache_date = "Cache Date "+string(asctime(curtime))+"\n";
		ofstream file("readme.txt");
		file<<cache_date;
		return;
	}
	string good = parent+"good/readme.txt";
	string bad = parent+"bad/readme.txt";
	string reg = parent+"regular/readme.txt";
	string redir = parent+"redirect/readme.txt";
	vector<string> readmes = {good, bad, reg, redir};

	time_t _tm = time(NULL);
	struct tm* curtime = localtime(&_tm);
	string cache_date = "Cache Date "+string(asctime(curtime))+"\n";

	for(int i=0; i<readmes.size(); i++){
		string temp = readmes[i];
		ofstream file(temp);
		file<<cache_date;
	}
}

//Create readme.txt files to hold info
void create_readme(string parent){
	string good = parent+"good/readme.txt";
	string bad = parent+"bad/readme.txt";
	string reg = parent+"regular/readme.txt";
	string redir = parent+"redirect/readme.txt";
	vector<string> readmes = {good, bad, reg, redir};

	time_t _tm = time(NULL);
	struct tm* curtime = localtime(&_tm);
	string cache_date = "Cache Date "+string(asctime(curtime))+"\n";

	for(int i=0; i<readmes.size(); i++){
		string temp = readmes[i];
		ofstream file(temp);
		file<<cache_date;
	}
}

//Remove a directoy in current folder
void remove_directory(string directory){
	char *p = new char[500];
	string path = get_path();
	string rm = "rm -rf ";
	string quote = "\"";
	string command = rm+quote+path+directory+quote;
	char *c = const_cast<char*>(command.c_str());
	system(c);
	return;
}

//Check if string "tag1" is within string "str"
bool isWithin(string &str, string tag1) {
	return (str.find(tag1) != string::npos);
}

// Parse the contents between a pair of tags
string parse(string &str, string tag1, string tag2) {
	size_t p1 = str.find(tag1);
	size_t p2 = str.find(tag2, p1);
  	if (p1 != string::npos and p2 != string::npos) {
  		return str.substr(p1+tag1.size(), p2-p1-tag1.size());
  	}
  	else {
  		return "";
  	}
}

// Populate the given vector with all matches, in given string, between given tags
// Returns the index immediately after last match (for purposes of block shifting)
int parse(string &str, string tag1, string tag2, vector<string> &result) {
	int pos = 0;                                            // Current position in string
	while(true) {
		size_t p1 = str.find(tag1, pos);
		size_t p2 = str.find(tag2, p1);
  		if (p1 != string::npos and p2 != string::npos) {    // If new match, push it back
  			pos = p2+tag2.size();
  			string parsed = str.substr(p1+tag1.size(), p2-p1-tag1.size());
  			result.push_back(parsed);
  		}
		else {break;}                                       // Break otherwise
	}
	return pos;
}

//Grab the number of pictures in article
short picCount(string &article){
	short count=0;
	bool condition=true;
	string pic = ".jpg";
	size_t location = 0;
	while(condition){
		location = article.find(pic, location);
		if(location!=string::npos){
			count++;
			location += pic.size();
		}
		else{
			condition=false;
		}
	}
	return count;
}

//Check article for cleanup templates
bool getTemplates(string &input, string &temp){
	vector<string> templates = {"{{Multiple issues", "stub}}", "{{Cleanup", "{{Advert", "{{Update", "{{Tone", "{{Plot", "{{Essay-like", "{{Peacock", "{{Technical", "{{Confusing"};
	vector<string> clean = {"multiple", "stub", "cleanup", "advert", "update", "tone", "plot", "essay-like", "peacock", "technical", "confusing"};
	for(int i=0; i<templates.size(); i++){
		if(input.find(templates[i]) != string::npos){
			temp = clean[i];
			return true;
		}
	}
	return false;
}

//Get redirection title
string getRedirect(string &input){
	string begin = "[[";
	string end = "]]";
	size_t location = input.find(begin);
	size_t endlocation = input.find(end, location+begin.size());
	string title = input.substr(location+begin.size(), endlocation-location-end.size());
	return title;
}

//Functions to recover wikiPages from files
void getFileHeaderTitle(ifstream &wikiFile, string &subject){
	string colon = ":";
	int size = colon.size();
	string line;
	getline(wikiFile, line);
	size_t location = line.find(colon);
	subject = line.substr(location+size+2, string::npos);
	return;
}

void getFileHeader(ifstream &wikiFile, string &subject){
	string colon = ":";
	int size = colon.size();
	string line;
	getline(wikiFile, line);
	size_t location = line.find(colon);
	subject = line.substr(location+size+1, string::npos);
	return;
}

void getFileHeader(ifstream &wikiFile, int &subject){
	string colon = ":";
	int size = colon.size();
	string line;
	getline(wikiFile, line);
	size_t location = line.find(colon);
	line = line.substr(location+size+1, string::npos);
	subject = std::stoi(line, nullptr);
	return;
}

void getFileHeader(ifstream &wikiFile, short &subject){
	string colon = ":";
	int size = colon.size();
	string line;
	getline(wikiFile, line);
	size_t location = line.find(colon);
	line = line.substr(location+size+1, string::npos);
	int temp = std::stoi(line, nullptr);
	subject = short(temp);
	return;
}

void getFileHeader(ifstream &wikiFile, bool &subject){
	string colon = ":";
	int size = colon.size();
	string line;
	getline(wikiFile, line);
	size_t location = line.find(colon);
	line = line.substr(location+size+1, string::npos);
	int sub = std::stoi(line, nullptr);
	subject=false;
	if(sub==1){
		subject=true;
	}
	return;
}






#endif // HELPERS_H