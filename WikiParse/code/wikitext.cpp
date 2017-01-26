#include "wikitext.h"


void copy_between(const string &body, const string &target, const vector<string> &endtargets, vector<string> &copies)
{
    // used in the read_citations function, parses all instances from "target" to the closest "endtarget" element
    // and pushes them into the "copies" parameter for the returning function to recieve
    while(true){
        size_t location = body.find(target);
        if(location!=string::npos){

            int closest_partner = 1000000000;
            int close_cut_at = -1;

            for (int i=0; i<endtargets.size(); i++){

                string endtarget = endtargets[i];
                size_t endlocation = body.find(endtarget, location+target.size());

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
            copies.push_back(body.substr(location,close_cut_at));
        }
        else{
            return;
        }
    }
}

void copy_between(const string &body, const string &target, const string &endtarget, vector<string> &copies)
{
    cout<<"\n"<<body<<"\n";
    // same idea as the vector version
    while(true)
    {
        size_t location = body.find(target);
        if(location!=string::npos){

            int closest_partner = 1000000000;
            int close_cut_at = -1;

            size_t endlocation = body.find(endtarget, location+target.size());

            if(endlocation!=string::npos){
                close_cut_at = endlocation+endtarget.size()-location;
                closest_partner = endlocation;
            }
        
            if (close_cut_at==-1){
                return;
            }

            copies.push_back(body.substr(location,close_cut_at));
        }
        else{
            return;
        }
    }
}

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