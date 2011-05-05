from collections import namedtuple, defaultdict
from csc_utils.prefixcode.process_text import ubernormalize
from csc_utils.ordered_set import OrderedSet
import re

Node = namedtuple('Node', ['value', 'freq', 'left', 'right'])
CHARACTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#'
ALPHANUM = re.compile(r'(^|[^0-9])([0-9])')

def merge_nodes(node1, node2):
    return Node(node1.value + node2.value,
                node1.freq + node2.freq,
                node1, node2)

def read_lexicon(filename):
    infile = open(filename)
    lex = []
    for line in infile:
        word = line.strip()
        lex.append(word)
    return lex

def make_tetragram_freqs(lexicon):
    tetragram_freqs = defaultdict(lambda: defaultdict(int))
    for word in lexicon:
        if ' ' not in word:
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
                show_prefix_code(codes, CODES[newkey], prefix, consumed, maxlen)
    if node.left:
        show_prefix_code(codes, node.left, prefix+'0', consumed, maxlen)
    if node.right:
        show_prefix_code(codes, node.right, prefix+'1', consumed, maxlen)
    
WORDS = read_lexicon('lexicon.txt')
FREQS = make_tetragram_freqs(WORDS)
CODES = {}
for char in CHARACTERS+'^':
    for char2 in CHARACTERS+'^':
        for char3 in CHARACTERS+'^':
            CODES[char+char2+char3] = make_prefix_code(FREQS[char+char2+char3])
LEXICON = OrderedSet(WORDS)

def prefix_to_binary(word, key='^^^', consumed='', length=12):
    """
    Get a binary value representing the prefix of a word, to be used in hash
    values.
    """
    if len(consumed) >= length:
        return consumed[:length]
    if key not in CODES:
        return (consumed + '1'*length)[:length]
    return _walk_prefix_tree(word+'$', key, CODES[key], consumed, length)

def binary_to_prefix(binary, key='^^^'):
    if not binary:
        return ''
    if key not in CODES:
        return ''
    return _walk_binary_tree(binary, key, CODES[key])

def _walk_binary_tree(binary, key, node):
    if node.left is None:
        val = ''
        if node.value != '#' and node.value != '$':
            val = node.value
        return val + binary_to_prefix(binary, (key+node.value)[-3:])
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
        return prefix_to_binary(word[1:], key[1:]+word[0], consumed, length)
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

def prefix_hash(text):
    """
    Given a short text (preferably no more than 2 or 3 words), get a
    20-bit hash value for that text.
    
    This is designed so that you can actually place it into one of 2**20
    buckets, and collisions will only occur between rare and very similar
    strings.
    """
    text = ALPHANUM.sub(r'\1#\2', ubernormalize(text))
    if text in LEXICON:
        # known word
        # format: binary 00 followed by 18-bit index number
        index = LEXICON.index(text)
        return index
    else:
        if ' ' in text:
            # multiple words
            # format: binary 1, 8-bit first part, 8-bit last part, 3-bit hash
            first, last = text.rsplit(' ', 1)
            first = first.replace(' ', '')
            bin1 = int(prefix_to_binary(first, length=8), 2)
            bin2 = int(prefix_to_binary(last, length=8), 2)
            hashval = hash((first, last)) % 8
            return (1<<19) + (bin1<<11) + (bin2<<3) + hashval
        else:
            # single word.
            # format: binary 01, 12-bit prefix, 6-bit hash
            binval = int(prefix_to_binary(text, length=12), 2)
            hashval = hash(text) % 64
            return (1<<18) + (binval<<6) + hashval

def prefix_unhash(val):
    """
    prefix_hash is a particularly reversible hash. In many cases, you will 
    be able to "unhash" it to exactly the same text that went in, or at least
    to an abbreviation of that text.

    This will return a unique, possibly human-readable string for each hash
    value. Do not use this for output, but feel free to use it for debugging.

    TODO: adjust prefix_hash so that the arbitrary prefix_unhash string
    actually unhashes to the same thing.
    """
    if val >= 1<<19:
        # multiple words
        bin1 = (val>>11) % 256
        bin2 = (val>>3) % 256
        hashval = val % 8
        binstr1 = '{0:08b}'.format(bin1)
        prefix1 = binary_to_prefix(binstr1)
        common1 = prefix_to_binary(prefix1)
        remain = '0' + binstr1[len(common1):]

        binstr2 = '{0:08b}'.format(bin2)
        prefix2 = binary_to_prefix(binstr2)
        common2 = prefix_to_binary(prefix2)
        remain += binstr2[len(common2):]

        residue = (int(remain, 2)<<3) + hashval
        return "{0}{1}~{2:o}".format(prefix1.title(), prefix2.title(), residue)
    elif val >= 1<<18:
        # single word
        val -= 1<<18
        binstr = '{0:012b}'.format(val >> 6)
        assert len(binstr) == 12
        prefix = binary_to_prefix(binstr)
        common = prefix_to_binary(prefix)
        hashval = val % 64
        residue = (int('0' + prefix[len(common):], 2)<<6) + hashval
        return "{0}~{1:o}".format(prefix.title(), residue)
    else:
        try:
            return LEXICON[val].lower()
        except IndexError:
            return '???'

def test_collisions(filename):
    buckets = {}
    for line in open(filename):
        text = line.strip().replace('_', ' ').split(',')[0]
        if text.count(' ') < 2:
            bucket = prefix_hash(text)
            if bucket in buckets:
                other = buckets[bucket]
                if ubernormalize(other) != ubernormalize(text):
                    print "Hash collision: %s, %s, %s" % (buckets[bucket],
                    text, prefix_unhash(bucket))
            buckets[bucket] = text
