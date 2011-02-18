try:
    # Works in Python 2.6
    bin
    def rev_bin(x): return ''.join(reversed(bin(x)[2:]))
except NameError:
    def rev_bin(x):
        '''
        Return the reverse of the binary representation of a number
        '''
        if x == 0: return '0'
        res = []
        while x > 0:
            res.append(str(x % 2))
            x = x >> 1
        return ''.join(res)

def sampling_sequence(lower=0.0, upper=1.0, initial=(0.0, 1.0)):
    '''
    This is actually called the binary van der Corput sequence. It's
    useful for sampling functions.

    >>> import itertools
    >>> list(itertools.islice(sampling_sequence(initial=None), 5))
    [0.5, 0.25, 0.75, 0.125, 0.625]

    But by default it starts with 0 and 1.

    >>> list(itertools.islice(sampling_sequence(), 5))
    [0.0, 1.0, 0.5, 0.25, 0.75]

    You can do different ranges too:

    >>> list(itertools.islice(sampling_sequence(-2, 2), 5))
    [-2.0, 2.0, 0.0, -1.0, 1.0]

    '''
    from itertools import count, chain
    rev_bin_seq = (rev_bin(x) for x in count(1))
    raw_seq = (float(int(x,2)) / (2**len(x)) for x in rev_bin_seq)

    # Scale the result
    scale = float(upper-lower)
    return (scale * val + lower for val in chain(initial or [], raw_seq))
