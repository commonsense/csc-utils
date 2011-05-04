from collections import namedtuple, defaultdict
import re

Node = namedtuple('Node', ['value', 'freq', 'left', 'right'])
CHARACTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#'

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

def make_tetragram_freqs(lexicon):
    tetragram_freqs = defaultdict(lambda: defaultdict(int))
    for word, freq in lexicon:
        # prefix all digit sequences with #.
        # strength in numbers, so to speak.
        count = 1
        word = re.sub(r'(^|[A-Z])([0-9])', r'\1#\2', word)
        if re.match(r'^#[0-9]+$', word):
            count = 100
        symbols = '^^^'+word+'$'
        for i in xrange(len(symbols)-3):
            first = symbols[i:i+3]
            second = symbols[i+3]
            tetragram_freqs[first][second] += count
    return tetragram_freqs

def make_prefix_code(freqs):
    queue = [Node('$', 0, None, None)]
    for char in freqs:
        if char != '$':
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
        show_prefix_tree(node.left, prefix+'0')
    if node.right:
        show_prefix_tree(node.right, prefix+'1')
    
def show_prefix_code(codes, node, prefix='', consumed='', maxlen=18):
    if len(prefix) > maxlen:
        return
    if node.left is None and node.value != '$':
        consumed += node.value
        print "%-20s %s" % (prefix, consumed)
        lookup_str = '^^'+consumed
        newkey = lookup_str[-3:]
        if newkey in codes:
            if node.value != '$':
                show_prefix_code(codes, codes[newkey], prefix, consumed, maxlen)
    if node.left:
        show_prefix_code(codes, node.left, prefix+'0', consumed, maxlen)
    if node.right:
        show_prefix_code(codes, node.right, prefix+'1', consumed, maxlen)
    
print 'lexicon'
lexicon = read_lexicon('unigrams-alph.txt')
print 'freqs'
freqs = make_tetragram_freqs(lexicon)
print 'code'
codes = {}
for char in CHARACTERS+'^':
    for char2 in CHARACTERS+'^':
        for char3 in CHARACTERS+'^':
            codes[char+char2+char3] = make_prefix_code(freqs[char+char2+char3])

def _prefix_to_binary(word, key='^^^', consumed='', length=12):
    """
    Get a binary value representing the prefix of a word, to be used in hash
    values.
    """
    if len(consumed) >= length:
        return consumed[:length]
    if key not in codes:
        return (consumed + '1'*length)[:length]
    return _walk_prefix_tree(word+'$', key, codes[key], consumed, length)

def _binary_to_prefix(binary, key='^^^'):
    if not binary:
        return ''
    return _walk_binary_tree(binary, key, codes[key])

def _walk_binary_tree(binary, key, node):
    if node.left is None:
        return node.value + _binary_to_prefix(binary, (key+node.value)[-3:])
    if not binary:
        return ''
    if binary[0] == '0':
        return _walk_binary_tree(binary[1:], key, node.left)
    else:
        return _walk_binary_tree(binary[1:], key, node.right)

def _walk_prefix_tree(word, key, node, consumed, length):
    if len(consumed) >= length:
        return consumed[:length]
    if node.left is None:
        return _prefix_hash(word[1:], key[1:]+word[0], consumed, length)
    else:
        char = word[0]
        if char in node.left.value:
            return _walk_prefix_tree(word, key, node.left, consumed+'0',
            length)
        elif char in node.right.value:
            return _walk_prefix_tree(word, key, node.right, consumed+'1',
            length)
        elif '$' in node.left.value:
            return _walk_prefix_tree(word, key, node.left, consumed+'0',
            length)
        else:
            return _walk_prefix_tree(word, key, node.right, consumed+'1',
            length)

