from csc_utils.seq import sampling_sequence
from itertools import islice
from csc_utils.cache import cached

__all__ = ['sampling_sequence', 'in_groups_of', 'run_doctests', 'cached']

def in_groups_of(size, iterator):
    iterator = iter(iterator)
    while True:
        acc = list(islice(iterator, size))
        if not acc:
            break
        yield acc

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

