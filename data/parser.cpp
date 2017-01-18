// the different use cases that are available in this file are separated 
// by the line comments below. summarized, they are:
// (1) parse_simple()		--> parses datadump & saves articles
// (2) parse_categories()	--> scans datadump for articles in certain cats
// (3) parse_meta() 		--> gets all article titles & categories
// (4) investigate_meta() 	--> gets largest categories and their articles

using namespace std;

#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <time.h> // time calculations
#include <unistd.h> //For getting cwd
#include <stdio.h> //For error reporting
#include <sys/stat.h> //To get system info
#include "wikiPage.h"
#include "helpers.h"

time_t exec_time = 0; // used to create diff dirs for each exec

//---------------------------------------------------------------------------------------------
//---------------------------------------------------------------------------------------------

// saves all articles to file, no support for >1 articles_per_file, helper function
// for the parse_simple function.
void save_simple(vector<wikiPage> &buf, int buffer_size, int articles_per_file, int pageCt)
{
	if (buf.size()<buffer_size){
		return;
	}
	// if 1 article per file just saving by article names
	if (articles_per_file==1){
		for (int i=0; i<buf.size(); i++){

			if (buf[i].text.size()<400){
				continue;
			}
			ofstream file("data/parsed/test-"+to_string(exec_time)+"/"+buf[i].title+".txt");
			buf[i].save(file);
		}
		buf.clear();
		return;
	}
}

// parse w/o complex dir structure (all in single dir), source is
// the single filename input. Tested only with articles_per_file=1
// WARNING: Don't run this with the full data dump as the input, it will
// probably crash the computer because it only can do a single article per file
void parse_simple(string filename,int buffer_size=1, int articles_per_file=1)
{
	ifstream data(filename);

	unsigned long long pageCt = 0;
	float pageCtFloat = 0;
	vector<wikiPage> buf;
	time_t start = clock();
	exec_time = time(0);
	string folder = "/data/parsed/test-"+to_string(exec_time);
	create_directory(folder);

	bool eof = false;
	bool leave_formatting = false;

	while(data.eof()==false){
		string page;
		getPage(data,eof,page);
		wikiPage temp(page,leave_formatting);
		buf.push_back(temp);
		save_simple(buf,buffer_size,articles_per_file,pageCt);
		pageCt++;
		pageCtFloat = pageCt;

		cout<<"\r                                                                        ";
		cout.flush();
		cout<<"\rPages parsed: \t"<<pageCt<<"\tArt/Second: "<<(pageCtFloat/((clock()-start)/CLOCKS_PER_SEC));
		cout.flush();
	}
	cout<<"\n";
	save_simple(buf,1,articles_per_file,pageCt);
}

//---------------------------------------------------------------------------------------------
//---------------------------------------------------------------------------------------------

// called by flush_category buffer function
void flush_single_buffer(vector<wikiPage> &buf, string &buf_cat, string dir)
{
	string filename = dir+buf_cat+"-"+to_string(time(0))+".txt";
	string content = "";
	for (int i=0; i<buf.size(); i++)
	{
		content += buf[i].text;
	}
	ofstream file(filename);
	file<<content;
}

// handles the saving of a buffer where all of the elements
// are of the same category, called by the save_categories function
void flush_category_buffer(vector<wikiPage> &buf, string &buf_cat, int articles_per_file)
{
	string dir = "data/parsed/test-"+to_string(exec_time)+"/";
	vector<wikiPage> file_buf;
	for (int i=0; i<buf.size(); i++)
	{
		file_buf.push_back(buf[i]);
		if (file_buf.size() >= articles_per_file)
		{
			flush_single_buffer(file_buf,buf_cat,dir);
			file_buf.clear();
		}
	}
	if (file_buf.size() > 0)
	{
		flush_single_buffer(file_buf,buf_cat,dir);
	}
}

// adds wikiPage temp to its appropriate buffer, called by parse_categories
void add_to_buf(vector<vector<wikiPage>> &buf, vector<string> &buf_names, string &cat, wikiPage &temp)
{
	for (int i=0; i<buf_names.size(); i++)
	{
		if (cat == buf_names[i])
		{
			buf[i].push_back(temp);
			return;
		}
	}
	// need to add another row to buf, cat has no elems
	vector<wikiPage> new_cat_buf;
	new_cat_buf.push_back(temp);
	buf.push_back(new_cat_buf);
	buf_names.push_back(cat);
}

// checks to see if a wikiPage contains the 'target' categories
string check_cats(vector<string> targ_cats, wikiPage &temp)
{
	vector<string> page_cats = temp.categories;
	for (int i=0; i<page_cats.size(); i++)
	{
		for (int j=0; j<targ_cats.size(); j++)
		{
			if (page_cats[i] == targ_cats[j])
			{
				return page_cats[i];
			}
		}
	}
	return "no matches";
}

// partner function for the parse_categories function below
void save_categories(vector<vector<wikiPage>> &buf, vector<string> &buf_cats, int buffer_size, int articles_per_file)
{
	for (int i=0; i<buf.size(); i++)
	{
		if (buf[i].size() >= buffer_size) // if we need to flush the buffer
		{
			flush_category_buffer(buf[i],buf_cats[i],articles_per_file);
			buf.erase(buf.begin()+i);
			buf_cats.erase(buf_cats.begin()+i);
			// calling recursively to avoid problems with for loop indices
			save_categories(buf,buf_cats,buffer_size,articles_per_file); 
		}
	}
}

// parse from a single filename file. Only the articles which fit into
// one of the categories specified will be saved. All articles of the same
// category will be bundled together when they are saved. Recommend large buffer
// and articles_per_file sizes. Each category will have it's own buffer. This can be
// run with the full data dump easily
void parse_categories(string filename, vector<string> categories, int buffer_size=10000, int articles_per_file=10000)
{
	ifstream data(filename);

	unsigned long long pageCt = 0;
	float pageCtFloat = 0;
	unsigned long long foundCt = 0;
	
	vector<vector<wikiPage>> buf; // holds the found pages w/ app. cats
	vector<string> buf_cats; // holds the cats for the items in each row of buf

	time_t start = clock();
	exec_time = time(0);
	string folder = "/data/parsed/test-"+to_string(exec_time);
	create_directory(folder);

	bool eof = false;
	bool leave_formatting = false;

	while(data.eof()==false){
		string page;
		getPage(data,eof,page);
		wikiPage temp(page,leave_formatting);

		if (temp.isJunk)
		{	
			cout<<"\r                                                                    ";
			cout<<"\rCaught junk page: "<<temp.title<<"\n";
			continue;
		}

		string match = check_cats(categories,temp);

		if (match != "no matches")
		{
			cout<<"\r                                                                    ";
			cout<<"\rFound "<<temp.title<<" in category "<<match<<"\n";
			add_to_buf(buf,buf_cats,match,temp);
			foundCt++;
		}

		save_categories(buf,buf_cats,buffer_size,articles_per_file);

		pageCt++;
		pageCtFloat = pageCt;

		cout<<"\r                                                                        ";
		cout.flush();
		cout<<"\rSearched:\t"<<pageCt<<"\tFound:\t"<<foundCt<<"\tArt/Second: "<<(pageCtFloat/((clock()-start)/CLOCKS_PER_SEC));
		cout.flush();
	}
	cout<<"\n";
	save_categories(buf,buf_cats,1,articles_per_file);
}

//---------------------------------------------------------------------------------------------
//---------------------------------------------------------------------------------------------

// partner function for the parse_meta function below
void save_meta(vector<wikiPage> &buf, int buffer_size, string &path, ofstream &readme)
{
	if (buf.size() >= buffer_size)
	{
		string filename = path+"/"+to_string(time(0))+".txt";
		cout<<"\r                                                                  ";
		cout<<"\rWriting to "<<filename<<"\n";
		ofstream file(filename);
		string content = "";
		for (int i=0; i<buf.size(); i++)
		{
			content += "[Title: "+buf[i].title+"]~~[Categories: ";
			for (int j=0; j<buf[i].categories.size(); j++)
			{
				content += buf[i].categories[j];
				if (j != buf[i].categories.size()-1)
				{
					content += " | ";
				}
			}
			content += "]\n";
		}
		file<<content;
		buf.clear();
		readme<<filename<<"\n"; // write filename to readme.txt file
	}
}

// goes through the provided wikipedia data dump and only extracts article
// titles and the categories each article belongs to. This data is then
// written to a single file once we have found buffer_size articles. If there are
// more articles than buffer_size articles in the provided data dump than several
// calls to save_meta will result in several output files being written
void parse_meta(string filename, int buffer_size=10000)
{
	ifstream data(filename);
	int refresh_rate = 100;

	unsigned long long pageCt = 0;
	float pageCtFloat = 0;
	
	vector<wikiPage> buf; // holds the found pages

	time_t start = clock();
	exec_time = time(0);
	string folder = "data/parsed/meta-"+to_string(exec_time);
	create_directory("/"+folder);
	ofstream readme(folder+"/readme.txt");

	bool eof = false;
	bool leave_formatting = false;

	while(data.eof()==false){
		string page; 
		getPage(data,eof,page); // fetch an unprepped page
		wikiPage wikipage_t(page,leave_formatting,"meta"); // parse page into wikiPage
		buf.push_back(wikipage_t); // add to buffer
		if (buf.size() >= buffer_size) { save_meta(buf,buffer_size,folder,readme); }
		pageCt++;
		pageCtFloat = pageCt;
		if (pageCt % refresh_rate == 0)
		{
		cout<<"\r                                                                                   ";
		cout.flush();
		cout<<"\rSearched:\t"<<pageCt<<"\tArt/Second: "<<(pageCtFloat/((clock()-start)/CLOCKS_PER_SEC));
		cout.flush();
		}
	}
	cout<<"\n";
	save_meta(buf,1,folder,readme);
}

//---------------------------------------------------------------------------------------------
//---------------------------------------------------------------------------------------------

// parses through the outputs of the save_meta use case to group together
// categories and find the largest in the data dump. NOTE: this does not 
// operate directly on the data dump file, the parse_meta use case must
// be run first to create the necessary files to allow this to work (the 
// files containing all article titles and their categories).
void investigate_meta()
{
	string path = "data/parsed/meta/";
	string readme = path+"readme.txt";
	vector<string> files = parse_lines(readme);
	cout<<"Found "<<files.size()<<" files...\n";
	category_handler my_cats;

	for (int i=0; i<files.size(); i++)
	{
		cout<<"Reading "<<path<<files[i]<<"...";
		cout.flush();
		vector<string> temp = parse_lines(path+files[i]);

		cout<<" found "<<temp.size()<<" entries.\n";
		cout<<"Adding entries to category manager... ";
		for (int k=0; k<temp.size(); k++)
		{
			string entry = temp[k];
			string title = parse(entry,"[Title: ", "]~~");
			string cats = parse(entry,"~~[Categories: ", "]");

			if (cats=="" or cats==" ")
			{
				continue; // no category for this article
			}
			my_cats.add_entry(title, cats);

			cout.flush();
			cout<<"\r                                                        ";
			cout<<"\rNumber of categories: "<<my_cats.cats.size();
			cout.flush();
		}
		cout<<"\n";
	}
	my_cats.save_results();
}

//---------------------------------------------------------------------------------------------
//---------------------------------------------------------------------------------------------


class category
{
public:
	string name; // name of category
	vector<string> alt_names; // pseudo-names
	
	//vector<category> parents; // parent categories
	vector<string> children; // child categories

	category(wikiPage input)
	{
		load(input);
	}

	void load(wikiPage &input)
	{
		children = input.categories;
		name = input.title;
	}

	void save(ofstream &file)
	{
		file<<"{\""+name+"\":[";
		for (int i=0; i<children.size(); i++)
		{
			file<<"\""<<children[i]<<"\"";
			if (i!=children.size()-1)
			{
				file<<",";
			}
		}
		file<<"]}";
	}
};

void check_for_save(vector<category> &buf, int save_per_file, string save_folder, bool force_save=false)
{
	if ((buf.size() >= save_per_file) or force_save)
	{
		string filename = save_folder+"/categories-"+to_string(time(0))+".json";
		ofstream file(filename);

		for (int i=0; i<buf.size(); i++)
		{
			buf[i].save(file);

			if (i!=buf.size()-1)
			{
				file<<"\n";
			}
		}
		buf.clear();
	}
}

// searches through the provided data dump file to find all of the articles which are 
// describing a category (for example, something like this: 
// https://en.wikipedia.org/wiki/Category:1950_in_New_Zealand). The data is saved to the meta/
// directory (same as investigate_meta outputs to)

void parse_categories_2(string datadump_filename, int save_count=100, int per_file=10000)
{
	// namespace 14 is alloted to Category pages
	string save_parent = "meta";
	string save_folder = save_parent+"/parse_categories_2-"+to_string(time(0));
	create_directory("/"+save_folder);

	int num_saved = 0;
	long long total_articles = 0;

	ifstream data(datadump_filename);
	bool eof = false;
	bool leave_formatting = false;

	vector<category> buf;

	while(data.eof()==false)
	{
		string page;
		getPage(data,eof,page); // fetch an unprepped page
		wikiPage wikipage_t(page,leave_formatting,"category");
		total_articles++;

		if (wikipage_t.title.find("Category:")!=string::npos)
		{

			category temp(wikipage_t);
			buf.push_back(temp);
			check_for_save(buf,per_file,save_folder);

			num_saved++;

			if (num_saved >= save_count)
			{
				check_for_save(buf,per_file,save_folder,true);
				return;
			}
		}

		cout.flush();
		//cout<<"\r                                                        ";
		cout<<"\rArticles searched: "<<total_articles<<", saved: "<<num_saved;
		cout.flush();
	}
}


//---------------------------------------------------------------------------------------------
//---------------------------------------------------------------------------------------------

int main()
{
	string filename = "data/sources/enwiki-latest-pages-articles.xml";

	parse_categories_2(filename,10000000);

	cout<<"\nClosing program...\n";
	return 1;
}