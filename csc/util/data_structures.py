def nested_list_items(ndarray):
    '''
    Returns the items generator used by nested_list_to_dict.
    '''
    if ndarray[0] is None or isinstance(ndarray[0], (int, float)):
        return (((idx,), val) for idx, val in enumerate(ndarray))
    else:
        return ((((idx,)+k), v) for idx, lst in enumerate(ndarray)
                for k, v in nested_list_items(lst))

def nested_list_to_dict(ndarray):
    '''
    Makes a dict of {index: value} out of a nested list or ndarray.

    >>> sorted(nested_list_to_dict([[1,2],[3,4]]).items())
    [((0, 0), 1), ((0, 1), 2), ((1, 0), 3), ((1, 1), 4)]
    >>> sorted(nested_list_to_dict([None, 3]).items())
    [((0,), None), ((1,), 3)]
    
    Since numpy ndarrays iterate over their rows, this seems to work
    for them also.
    '''
    return dict(nested_list_items(ndarray))

def copy(obj):
    """
    Make a copy of obj if it's mutable. Handles a few common data types.

    >>> print copy(None)
    None

    >>> a = [1, 2]
    >>> b = copy(a)
    >>> b == a
    True
    >>> b[1] = 0
    >>> b == a
    False
    
    >>> from csc.divisi.ordered_set import OrderedSet
    >>> a = OrderedSet(['a', 'b', 'c'])
    >>> b = copy(a)
    >>> b == a
    True
    >>> b[1] = 'd'
    >>> b == a
    False
    """
    if obj is None or isinstance(obj, tuple) or isinstance(obj, basestring):
        return obj
    elif isinstance(obj, list):
        return obj[:]
    else:
        return obj.copy()

