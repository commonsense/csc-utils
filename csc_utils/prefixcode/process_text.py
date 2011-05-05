import simplenlp
import re
en = simplenlp.get('en')

alphanum_filter = re.compile(r'[^A-Z0-9 ]')
space_filter = re.compile(r'  +')

def ubernormalize(term):
    term = term.replace('_', ' ')
    return space_filter.sub(' ', alphanum_filter.sub('', en.normalize(term).upper())).strip()

