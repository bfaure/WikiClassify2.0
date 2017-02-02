#include "string_utils.h"

/*  Trim command taken from: 
    https://stackoverflow.com/questions/216823/whats-the-best-way-to-trim-stdstring */

string trim(string &s) {
   auto wsfront = find_if_not(s.begin(),s.end(),[](int c){return isspace(c);});
   auto wsback  = find_if_not(s.rbegin(),s.rend(),[](int c){return isspace(c);}).base();
   return (wsback<=wsfront?string():string(wsfront,wsback));
}

unsigned parse_all(const string &str, const string &tag1, const string &tag2, vector<string> &result) {
    size_t p1 = str.find(tag1);
    size_t p2;
    while (p1!=string::npos) {
        p1 += tag1.length();
        p2  = str.find(tag2, p1);
        if (p2!=string::npos) {
            result.push_back(str.substr(p1, p2-p1));
            p1 = str.find(tag1, p2+tag2.length());
        }
        else {
            return p1;
        }
    }
    return p2;
}

unsigned save_all(const string &str, const string &tag1, const string &tag2, void (*f)(string, database&, long long unsigned int&), database &db, unsigned long long &articles_read, unsigned long long &articles_saved) {
    size_t p1 = str.find(tag1);
    size_t p2;
    while (p1!=string::npos) {
        articles_read++;
        p1 += tag1.length();
        p2  = str.find(tag2, p1);
        if (p2!=string::npos) {
            f(str.substr(p1, p2-p1), db, articles_saved);
            p1 = str.find(tag1, p2+tag2.length());
            
        }
        else {
            return p1;
        }
    }
    return p2;
}

void parse(const string &str, const string &tag1, const string &tag2, string &result) {
    size_t p1 = str.find(tag1);
    if (p1!=string::npos) {
        p1       += tag1.length();
        size_t p2 = str.find(tag2, p1);
        if (p2!=string::npos) {
            result = str.substr(p1, p2-p1);
        }
    }
}

unsigned count_text(const string &str, const string &tag) {
    unsigned counter = 0;
    size_t p = str.find(tag);
    while (p!=string::npos) {
        p += tag.length();
        p = str.find(tag, p);
        counter ++;
    }
    return counter;
}