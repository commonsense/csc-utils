from csc.util.batch import chunk, Status, ForEach, foreach, queryset_foreach
from csc.util.cache import cached
from csc.util.seq import sampling_sequence

__all__ = ['chunk', 'Status', 'ForEach', 'foreach', 'queryset_foreach', 'cached', 'sampling_sequence']

def register_admin(module_name, model_class_names):
    # I think this was actually a bad idea. It will be going away sometime.
    from django.contrib import admin
    module = __import__(module_name, {}, {}, [''])
    for model_class_name in model_class_names:
        model = getattr(module, model_class_name)
        admin_class = getattr(module, model_class_name+'Admin', None)
        admin.site.register(model, admin_class)

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

