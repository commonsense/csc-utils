import re
import simplenlp
en = simplenlp.get('en')
alphanum_filter = re.compile(r'[^A-Z0-9 ]')
space_filter = re.compile(r'  +')

def ubernormalize(term):
    return space_filter.sub(' ', alphanum_filter.sub('', en.normalize(term).upper()))

def read_wordlist(filename):
    return set([ubernormalize(x.strip()) for x in open(filename).readlines()])
