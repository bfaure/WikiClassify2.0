#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#                          Standard imports
#-----------------------------------------------------------------------------#
from subprocess import call

#                            Main function
#-----------------------------------------------------------------------------#

def compile_parser():
    print("Compiling parser...")
    call(["g++","--std=c++11","-Wno-deprecated-declarations","-O3","WikiParse/code/main.cpp","WikiParse/code/string_utils.cpp", "WikiParse/code/wikidump.cpp", "WikiParse/code/wikipage.cpp", "WikiParse/code/wikitext.cpp", "WikiParse/code/database.cpp","-l","sqlite3"])

def run_parser(dump_path, destination_path):
    print("Running parser...")
    call(["./a.out", dump_path, destination_path])

def parse_wikidump(dump_path, destination_path):
    compile_parser()
    run_parser(dump_path, destination_path)