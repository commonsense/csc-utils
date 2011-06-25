from csc_utils.cache import cached
from csc_utils.seq import sampling_sequence

#__all__ = ['chunk', 'Status', 'ForEach', 'foreach', 'queryset_foreach', 'cached', 'sampling_sequence']

def in_groups_of(size, iterator):
    counter = 0
    acc = []
    for item in iterator:
        acc.append(item)
        counter += 1
        if counter == size:
            yield acc
            acc = []
            counter = 0
    if acc: yield acc

def run_doctests(mod):
    """
    Run the doctests in a module. This is a great thing to call from a
    `test.py` file that you run with nosetests.

    The module may contain a function called :meth:`doctest_globals` that
    returns a dictionary. This function will be run first and its results will
    become the global environment for the doctests.
    """
    import doctest
    extraglobs = {}
    if hasattr(mod, 'doctest_globals'): extraglobs = mod.doctest_globals()
    failed, attempted = doctest.testmod(mod, extraglobs=extraglobs)
    assert failed == 0

