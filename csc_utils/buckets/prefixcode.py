from collections import namedtuple, defaultdict
import re

Node = namedtuple('Node', ['value', 'freq', 'left', 'right'])
CHARACTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ#'

def merge_nodes(node1, node2):
    return Node(node1.value + node2.value,
                node1.freq + node2.freq,
                node1, node2)

def read_lexicon(filename):
    infile = open(filename)
    lex = []
    for line in infile:
        word, freq = line.strip().split(',')
        freq = int(freq)
        lex.append((word, freq))
    return lex

def make_bigram_freqs(lexicon):
    bigram_freqs = defaultdict(lambda: defaultdict(int))
    for word, freq in lexicon:
        symbols = re.sub(r'[0-9]', '#', '^'+word)
        for i in xrange(len(symbols)-1):
            first = symbols[i]
            second = symbols[i+1]
            bigram_freqs[first][second] += freq
    return bigram_freqs

def make_prefix_code(freqs):
    queue = []
    for char in CHARACTERS:
        freq = freqs[char]
        queue.append(Node(char, freq, None, None))
    while len(queue) > 1:
        queue.sort(key=lambda node: node.freq)
        first = queue[0]
        second = queue[1]
        rest = queue[2:]
        queue = [merge_nodes(first, second)] + rest
    return queue[0]

def show_prefix_tree(node, prefix=''):
    if node.left is None:
        print prefix, '\t', node.value
    if node.left:
        show_prefix_code(node.left, prefix+'0')
    if node.right:
        show_prefix_code(node.right, prefix+'1')
    
def show_prefix_code(codes, node, prefix='', consumed='', maxlen=18):
    if len(prefix) > maxlen:
        return
    if node.left is None:
        consumed += node.value
        print "%-20s %s" % (prefix, consumed)
        show_prefix_code(codes, codes[node.value], prefix, consumed, maxlen)
    if node.left:
        show_prefix_code(codes, node.left, prefix+'0', consumed, maxlen)
    if node.right:
        show_prefix_code(codes, node.right, prefix+'1', consumed, maxlen)
    
print 'lexicon'
lexicon = read_lexicon('unigrams-alph.txt')
print 'freqs'
freqs = make_bigram_freqs(lexicon)
print 'code'
codes = {}
codes['^'] = make_prefix_code(freqs['^'])
for char in CHARACTERS:
    print '\t', char
    codes[char] = make_prefix_code(freqs[char])

show_prefix_code(codes, codes['^'], maxlen=9)

