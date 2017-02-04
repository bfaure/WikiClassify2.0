#include "wikidump.h"
#include "wikipage.h"
#include "string_utils.h"
#include "database.h"

void read_page(string page, database &db, unsigned long long &articles_saved) {
    wikipage wp(page);
    if (db.add()) {
        articles_saved++;
    }
}

//bool wikipage::save_json(ofstream &file)
//{
//    // outputs in json format on a single line of the file
//    if(!text.empty())
//    {
//        if(is_disambig())
//        {
//            return false;
//        }
//
//        string divider = "";
//        if (first_save==false) { divider = ",\n"; }
//        if (first_save==true) { first_save = false; }
//        string output = divider;
//
//        output += "\""+to_string(ID)+"\":{";                // {id:{
//        output += "\"title\":\""+title+"\",";              // title:"Article title",
//        output += "\"ns\":\""+ns+"\",";                         // ns:Article namespace,
//        output += "\"timestamp\":\""+timestamp+"\",";           // timestamp:Article timestamp,
//
//        output += "\"contributor\":\""+contributor+"\","; // 
//
//        output += "\"size\":\""+to_string(text.size())+"\","; // size of the article text    
//        output += "\"instance_of\":\""+instance+"\",";   // instance_of:"Article instance_of",
//        output += "\"quality\":\""+quality+"\",";
//        output += "\"importance\":\""+importance+"\",";
//        output += "\"daily_views\":\""+daily_views+"\",";
//        output += "\"text\":\""+text+"\",";
//        output += "\"categories\":[";
//        for (int i=0; i<categories.size(); i++)
//        {
//            output += "\""+categories[i]+"\"";
//            if (i!=categories.size()-1)
//            {
//                output += ",";
//            }
//        }
//        output += "],";
//        output += "\"cited_domains\":[";
//        for (int i=0; i<citations.size(); i++)
//        {
//            string cur = citations[i].get_url();
//            if (cur==" " or cur=="" or cur=="None") // if the current url is empty
//            {
//                if (i==citations.size()-1) // if this is the last iteration
//                {
//                    if (output.at(output.size()-1)==',')
//                    {
//                        output.erase(output.size()-1); // erase the extra comma
//                    }
//                }
//                continue;
//            }
//
//            output += "\""+cur+"\"";
//            if (i!=citations.size()-1)
//            {
//                output += ",";
//            }
//        }
//        output += "],";
//        output += "\"cited_authors\":[";
//        for (int i=0; i<citations.size(); i++)
//        {
//            string cur = citations[i].get_author();
//            if (cur==" " or cur=="" or cur=="None") // if the current author is empty
//            {
//                if (i==citations.size()-1) // if this is the last iteration
//                {
//                    if (output.at(output.size()-1)==',') // if there is an extra comma 
//                    {
//                        output.erase(output.size()-1); // erase the extra comma
//                    }
//                }
//                continue;
//            }
//            output += "\""+cur+"\""; // add the current author to the output string
//            if (i!=citations.size()-1) // if this is not the last iteration
//            {
//                output += ","; // add comma between author names
//            }
//        }
//        output += "]";
//        output += "}";
//        file<<output;
//    }
//    return true;
//}

wikidump::wikidump(string path) {
    dump_input  = ifstream(path, ifstream::binary);
    if (dump_input.is_open()) {
        dump_size = ifstream(path, ifstream::ate | ifstream::binary).tellg();
    }
    else {
        cout<<"Could not open dump! ("<<path<<")"<<endl;
    }
}

void wikidump::read(string destination) 
{

    database dump_output(destination);

    articles_read = 0;
    articles_saved = 0;

    streampos offset; 
    const streampos buffer_size = 2000000;
    char buffer[(unsigned)buffer_size];
    
    time_t start_time = time(0);
    int display_refresh_rate = 5; // every 5 seconds, clear the output line
    
    while (dump_input.read(buffer, sizeof(buffer)))
    {
        offset = save_all(buffer, "\n  <page>\n", "\n  </page>\n", read_page, dump_output, articles_read, articles_saved);
        dump_input.seekg(dump_input.tellg()-buffer_size+offset);
        if (time(0)-start_time % display_refresh_rate == 0)
        {
            cout.flush();
            cout<<"\r";
            cout.flush();
        }
        cout.flush();
        cout<<"\r"<<(int)100.0*dump_input.tellg()/dump_size<<"% done, "<<time(0)-start_time<<" seconds elapsed, "<<articles_read<<" articles read, "<<articles_read-articles_saved<<" articles were not saved";
        cout.flush();
    }

    cout<<"\n";
}