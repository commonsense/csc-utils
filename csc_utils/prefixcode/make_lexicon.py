import re
import codecs
from csc_utils.prefixcode.process_text import ubernormalize

def read_wordlist(filename):
    return set([ubernormalize(x.strip()) for x in open(filename).readlines()])

def write_lexicon(filename):
    conceptnet = read_wordlist('concepts.txt')
    wordnet = read_wordlist('wordnet.txt')
    enable = read_wordlist('enable.txt')
    lexicon = conceptnet | wordnet | enable
    
    out = codecs.open(filename, 'w', encoding='utf-8')
    for item in sorted(lexicon):
        print >> out, item
    out.close()

if __name__ == '__main__':
    write_lexicon('lexicon.txt')

