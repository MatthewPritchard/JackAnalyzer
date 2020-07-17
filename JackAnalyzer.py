#!/usr/bin/python3
from sys import argv
import os
from JackTokenizer import Tokenizer
from CompilationEngine import Compiler

# Jack Analyzer, Analyzes Jack, obviously
if __name__ == "__main__":
    path = os.path.abspath(argv[1])

    if os.path.isdir(path):
        tokenizers = [Tokenizer(os.path.join(path, filename)) for filename in os.listdir(path) if filename.endswith(".jack")]
    elif os.path.isfile(path):
        tokenizers = [Tokenizer(argv[1])]
    else:
        raise IOError("not a file or directory")
    
    for tokenizer in tokenizers:
        Compiler(tokenizer)
