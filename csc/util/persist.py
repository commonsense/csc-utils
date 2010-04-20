import os.path
import cPickle as pickle
import base64
import logging
import itertools
from UserDict import DictMixin as DictMixin_

# Hack: Make DictMixin a new-style class.
class DictMixin(object, DictMixin_): pass

def pkl_find_global(module_name, class_name):
    if module_name == 'csc.conceptnet4.analogyspace' and 'Tensor' in class_name:
        logging.warn("Transforming a special CNet tensor into just a plain old LabeledView.")
        from csc.divisi.labeled_view import LabeledView
        return LabeledView
    return getattr(__import__(module_name, None, None, ['']), class_name) # FIXME: not exactly the right way to import a module.

def unpickle(f):
    if isinstance(f, basestring): f = open(f, 'rb')
    unpickler = pickle.Unpickler(f)
    unpickler.find_global = pkl_find_global
    return unpickler.load()

def get_picklecached_thing(filename, func=None, name=None):
    # This functionality is superceded by PickleDict.get_lazy.
    if name is None: name = filename
    if filename.endswith('.gz'):
        import gzip
        opener = gzip.open
    else:
        opener = open
    try:
        f = opener(filename, 'rb')
        print 'Loading', name
        result = unpickle(f)
        f.close()
    except IOError:
        if func is None: raise
        print 'Computing', name
        result = func()
        print 'Saving', name
        f = opener(filename, 'wb')
        pickle.dump(result, f, -1)
        f.close()
    return result

# the short, 1-argument version that Rob wants because pickle.load
# isn't easy enough
def load_pickle(filename):
    return get_picklecached_thing(filename)

# List of things never to try to forward to the base object, because they're
# just part of various dynamic introspection stuff. (er... IPython.)
i2a_blacklist = set(('_getAttributeNames', 'trait_names'))
# And always pass these through
i2a_passthrough = set(('mkdir','rename'))

class ItemToAttrAdaptor(object):
    def __init__(self, obj):
        '''
        Operations to attributes on this object translate to operations on
        items in obj.

        Except when you retrieve a PickleDict; then you get another ItemToAttrAdaptor.
        '''
        self._obj = obj

    def __repr__(self):
        return 'ItemToAttrAdaptor(%r)' % (self._obj,)

    def __getattr__(self, key):
        if key in i2a_blacklist: raise AttributeError(key)
        if key in i2a_passthrough and hasattr(self._obj, key):
            return getattr(self._obj, key)
        res = self._obj[key]
        return res if not isinstance(res, PickleDict) else res.d
    
    def __setattr__(self, key, val):
        if key.startswith('_') or key in i2a_blacklist:
            return super(ItemToAttrAdaptor, self).__setattr__(key, val)
        self._obj[key] = val

    def __delattr__(self, key):
        del self._obj[key]

    def __dir__(self):
        # This is only useful for Python 2.6+.
        return self._obj.keys() + [x for x in i2a_passthrough if hasattr(self._obj, x)]

import weakref
class MaybeWeakValueDict(DictMixin):
    '''
    weakref.WeakValueDictionary is awesome, except that you can't store certain things in it.

    So this keeps a WeakValueDictionary and a fallback dict.

    >>> w = weakref.WeakValueDictionary()
    >>> w[1] = 1
    Traceback (most recent call last):
       ...
    TypeError: cannot create weak reference to 'int' object

    >>> aset = set([1,2,3])
    >>> w[1] = aset # (ok)

    >>> d = MaybeWeakValueDict()
    >>> d[1] = 1
    >>> d[1] = aset
    >>> d[1]
    set([1, 2, 3])
    >>> 1 in d
    True
    >>> del d[1]
    >>> 1 in d
    False
    
    '''
    def __init__(self, dct=None):
        self.weak = weakref.WeakValueDictionary()
        self.normal = dict()
        if dct is not None:
            self.update(dct)

    def __getitem__(self, key):
        if key in self.weak:
            return self.weak[key]
        return self.normal[key]

    def __setitem__(self, key, val):
        if key in self:
            del self[key]
        try:
            self.weak[key] = val
        except TypeError:
            self.normal[key] = val

    def __delitem__(self, key):
        if key in self.weak:
            try:
                del self.weak[key]
            except KeyError: pass # just in case the garbage collector ran.
            assert key not in self.normal
        else:
            del self.normal[key]

    def has_key(self, key):
        return key in self.weak or key in self.normal

    def __iter__(self):
        return itertools.chain(self.weak, self.normal)

    
            
    
def human_readable_size(sz, multiplier=1000, sizes=['B', 'kB', 'MB', 'GB']):
    '''
    Returns a "human-readable" formatting of a number of bytes.

    >>> human_readable_size(5)
    '5.00B'
    >>> human_readable_size(1500)
    '1.50kB'
    >>> human_readable_size(1500*1000)
    '1.50MB'
    '''
    for name in sizes:
        if sz < multiplier:
            break
        sz = sz / float(multiplier)
    return '%.2f%s' % (sz, name)

def get_ipython_history(num_entries=15):
    from IPython import ipapi
    ip = ipapi.get()
    if ip is None: return None
    input_lines = [item.strip() for item in ip.user_ns['In']]
    return [item for item in input_lines
            if item and not item.startswith('?') and not item.endswith('?')][-num_entries:]
    

class PickleDict(DictMixin):
    '''
    A PickleDict is a dict that dumps its values as pickles in a
    directory. It makes a convenient dumping ground for temporary
    data.

    >>> import tempfile
    >>> dirname = tempfile.mkdtemp()
    >>> pd = PickleDict(dirname)

    Let's clear out the directory so the tests start from a known state.
    
    >>> pd._clear()

    >>> pd['abc'] = 123
    >>> pd['abc']
    123

    It keeps an internal cache, so to make sure it's actually storing
    persistently, let's make a new one.

    >>> pd = PickleDict(dirname)
    >>> pd['abc']
    123

    It behaves like a dictionary:

    >>> pd.keys()
    ['abc']
    >>> pd.items()
    [('abc', 123)]

    If you're just using string keys, you can use the item-to-attr
    adaptor `d`:

    >>> pd.d.abc
    123
    >>> pd.d.key = 'val'
    >>> del pd.d.abc

    But unlike a normal Python dict, if you change the contents of a
    list or dict or Tensor that you've pickled, PickleDict won't know
    that you changed it, unless you tell it:

    >>> pd.d.a = [1, 2, 3]
    >>> pd.d.a.append(4)
    >>> pd.d.a = pd.d.a # Force a re-store

    Or you can explicitly say that something changed:

    >>> pd.changed('a')
    >>> pd.changed() # re-writes everything that's in the cache.
    
    PickleDict actually supports any hashable item as a key, by
    pickling then base64-encoding the key (prepending a `:`). If you
    see a bunch of odd-looking files, that's where they came from.

    >>> pd[1,2,3] = 4,5,6
    >>> pd[':abc'] = 'abc' # just to test...
    >>> pd.clear_cache()
    >>> ':abc' in pd.keys()
    True

    Subdirectories are also supported:

    >>> subdir = pd.mkdir('sub')
    >>> pd['sub'][7,8] = 9, 10
    >>> subdir[7,8]
    (9, 10)

    And you can rename things:

    >>> pd.rename('sub', 'dir2')
    >>> pd['dir2'][7, 8]
    (9, 10)

    It can also lazily compute an expensive function only if the
    result is not already pickled. (This replaces
    get_picklecached_thing.)

    >>> def thunk():
    ...     print 'Expensive calculation...'
    ...     return 42
    ... 
    >>> pd.get_lazy('the_answer', thunk)
    Expensive calculation...
    42
    >>> pd.get_lazy('the_answer', thunk)
    42
    >>> 'the_answer' in pd
    True

    Metadata is stored in a _meta subdirectory, as pickled
    dictionaries. One thing stored is the type of the object, so you
    don't have to load it to see what type it is.

    >>> pd['_meta']['the_answer']['type'] == str(int)
    True

    If you were running from within IPython, the metadata dict also
    includes 'context', which holds your last 15 IPython inputs.

    There's a friendlier interface to getting metadata too:

    >>> pd.get_meta('the_answer', 'type') == str(int)
    True
    >>> pd.get_meta('the_answer', 'unknown_key', 'default value')
    'default value'
    >>> pd.set_meta('the_answer', 'unknown_key', 'known value')
    >>> pd.get_meta('the_answer', 'unknown_key', 'default value')
    'known value'
    
    '''
    special_character = '+'
    __slots__ = ['logger', 'log', 'dir', 'gzip', 'store_metadata', 'history_len', 'cache']
    
    def __init__(self, dir, gzip=True, store_metadata=True, log=True, context_history_len=20):
        self.logger = logging.getLogger('csc.util.persist.PickleDict')
        self.log = log
        self.dir = os.path.abspath(os.path.expanduser(dir))
        self.gzip = gzip
        self.store_metadata = store_metadata
        self.history_len = context_history_len
        if not os.path.isdir(self.dir):
            os.makedirs(self.dir)
        self.clear_cache()
        if store_metadata:
            self['_meta']
            self.cleanup_meta()

    def __repr__(self):
        return 'PickleDict(%r)' % self.dir

    @property
    def d(self): return ItemToAttrAdaptor(self)
    
    def path_for_key(self, key):
        # FIXME: This method is hugely inefficient but for the moment necessary.
        #
        # Details: Pickles are not canonical. For example, the tuple
        # ('BroadcastName',) pickles to both
        # '\x80\x02U\rBroadcastName\x85q\x01.' and
        # '\x80\x02U\rBroadcastNameq\x01\x85q\x02.'. Both were
        # cPickle.dumps(key, -1). I think one was from Py2.5 and the
        # other Py2.6, but I'm not sure. In any case, the only thing
        # we can rely on is that _un_pickling produces __eq__ual
        # results.
        #
        # The right way to solve this probably involves using the
        # hash() as the key to a second collection.
        if not isinstance(key, basestring) or key.startswith(self.special_character) or '/' in key:
            for filename in os.listdir(self.dir):
                if not filename.startswith(self.special_character): continue
                if self.key_for_path(filename) == key:
                    key = filename
                    break
            else:
                # Didn't break out of the loop, so key wasn't found. Make a new one.
                key = self.special_character+base64.urlsafe_b64encode(pickle.dumps(key, -1))
        return os.path.join(self.dir, key)

    def key_for_path(self, path):
        if path.startswith(self.special_character):
            return pickle.loads(base64.urlsafe_b64decode(path[1:]))
        return path

    def clear_cache(self):
        self.cache = {} #MaybeWeakValueDict()

    def _load(self, key):
        '''
        Just load some data, bypassing the cache.
        '''
        path = self.path_for_key(key)
        if self.store_metadata and key == '_meta':
            return MetaPickleDict(path)

        if os.path.isdir(path):
            # Keep sub-PickleDict objects in cache, so that they
            # can cache their own data.
            return PickleDict(path, gzip=self.gzip, store_metadata=self.store_metadata)
        if not os.path.exists(path):
            raise KeyError(key)
        if self.log: self.logger.info('Loading %r...', key)
        try:
            import gzip
            data = unpickle(gzip.open(path))
        except IOError:
            data = unpickle(open(path))

        if self.log: self.logger.info('Loaded %r (%s).', key, type(data))
        return data
        
        
    def __getitem__(self, key):
        if key in self.cache:
            return self.cache[key]
        else:
            data = self._load(key)
            self.cache[key] = data
            return data
    
    def __setitem__(self, key, val):
        if self.log: self.logger.info('Saving %r...', key)
        self.cache[key] = val
        import gzip
        opener = gzip.open if self.gzip else open
        f = opener(self.path_for_key(key), 'wb')
        pickle.dump(val, f, -1)
        if self.log: self.logger.info('Saved %r (%s)', key, human_readable_size(f.tell()))
        f.close()

        if self.store_metadata:
            meta = {}
            meta['type'] = str(type(val))

            # Add IPython history
            try:
                meta['context'] = get_ipython_history(num_entries=self.history_len)
            except ImportError:
                pass
            self['_meta'][key] = meta

    def __delitem__(self, key):
        self.cache.pop(key, None) # don't fail if it's not cached.
        os.remove(self.path_for_key(key))


    def _nuke(self):
        '''
        Destroy the directory tree, aka, ``rm -rf``.
        '''
        import shutil
        shutil.rmtree(self.dir)
        
        
    def _clear(self):
        '''
        Clear everything in the directory.
        '''
        self._nuke()
        os.makedirs(self.dir)
        self.clear_cache()

    
    def clear(self):
        raise NotImplementedError("`clear`? Do you really mean that? If so, run _clear instead.")
    
    def changed(self, name=None, ignore_not_present=False):
        if name is None:
            for k, v in self.cache.iteritems():
                if not isinstance(v, PickleDict):
                    self[k] = v
        else:
            if name not in self.cache and not ignore_not_present:
                raise KeyError('%s was not cached (so it could not have been changed in memory).' % name)
            self[name] = self.cache[name]
        
    def mkdir(self, name):
        os.mkdir(self.path_for_key(name))
        return self[name]

    def subdir(self, name):
        if name not in self:
            self.mkdir(name)
        assert isinstance(self[name], PickleDict)
        return self[name]

    def rename(self, old, new):
        os.rename(self.path_for_key(old), self.path_for_key(new))
        if old in self.cache:
            if not isinstance(self.cache[old], PickleDict):
                self.cache[new] = self.cache[old]
            del self.cache[old]
        if '_meta' in self and old in self['_meta']:
            self['_meta'].rename(old, new)


    def __iter__(self):
        return (self.key_for_path(filename) for filename in os.listdir(self.dir) if filename != '_meta')

    def keys(self):
        return list(self.__iter__())

    def has_key(self, key):
        return (self.store_metadata and key == '_meta') or os.path.exists(self.path_for_key(key))

    def get_meta(self, key, meta_key, default_value=None):
        try:
            return self['_meta'][key][meta_key]
        except KeyError:
            return default_value

    def set_meta(self, key, meta_key, value):
        meta = self['_meta']
        meta_for_key = meta.get(key, {})
        meta_for_key[meta_key] = value
        meta[key] = meta_for_key
        
    def cleanup_meta(self):
        meta = self['_meta']
        keys = set(self.iterkeys())
        for m in meta.keys():
            if m not in keys:
                self.logger.info('Removing orphan metadata for %r' % m)
                del meta[m]

    # this is the replacement for get_picklecached_thing:
    def get_lazy(self, key, thunk, version=None):
        if version is not None and not self.store_metadata:
            raise ValueError("Can't store version if we're not storing metadata.")
        if version is None: version = 0
        
        if key in self and self.get_meta(key, 'version', 0) == version:
            #logging.info('get_lazy: found %r.' % (key,))
            return self[key]

        if self.log: self.logger.info('get_lazy: computing %r.' % (key,))
        return self._compute(key, thunk, version)

    def _compute(self, key, thunk, version):
        result = thunk()
        self[key] = result
        self.set_meta(key, 'version', version if version is not None else 0)
        return self[key]

    def lazy(self, name=None, version=None):
        '''
        Returns a lazy decorator that takes a thunk, returns a thunk
        that loads it if it's in the PickleDict, or calls the function
        and stores the result if not.

        >>> import tempfile
        >>> dirname = tempfile.mkdtemp()
        >>> pd = PickleDict(dirname)
        >>> @pd.lazy()
        ... def answer():
        ...     print 'Expensive calculation...'
        ...     return 42
        ...
        >>> answer()
        Expensive calculation...
        42

        If you changed the code and want it to re-calculate, increment version; version=0 is the default:

        >>> @pd.lazy(version=0)
        ... def answer():
        ...     print 'Expensive calculation...'
        ...     return 43
        ...
        >>> answer()
        42

        Now increment it to say we changed it.
        
        >>> @pd.lazy(version=1)
        ... def answer():
        ...     print 'Expensive calculation...'
        ...     return 43
        ...
        >>> answer()
        Expensive calculation...
        43

        You can also force a recalculation:

        >>> answer()
        43
        >>> answer.recalculate()
        Expensive calculation...
        43
        '''
        from functools import wraps
        def dec(thunk): # gets called with the actual thunk
            # nonlocal name # save it for Py3.0...
            if name is None: key = thunk.__name__
            else: key = name

            @wraps(thunk)
            def f():
                return self.get_lazy(key, thunk, version)
            
            def recalculate():
                return self._compute(key, thunk, version)
            recalculate.__doc__ = 'Unconditionally recalculates %s, and stores and returns the result.' % key
            f.recalculate = recalculate
            f.func = thunk
            return f
        return dec

    def lazy_dir(self, name=None):
        from functools import wraps
        def dec(thunk):
            if name is None: key = thunk.__name__
            else: key = name
            @wraps(thunk)
            def f():
                if key in self:
                    return self[key]
                else:
                    res = dict(thunk())
                    pd = self.subdir(key)
                    pd.update(res)
                    return pd
            return f
        return dec
    
    def lazy_loader(self, name):
        '''
        Returns a function that lazily loads some data. Like `lazy`,
        but without the means to compute it.

        e.g., conceptnet_tensor = lazy_loader('conceptnet_tensor')
        '''
        def thunk():
            return self[name]
        thunk.__name__ = name
        thunk.__doc__ = 'Lazily loads %r from %r.' % (name, self)
        return thunk

class MetaPickleDict(PickleDict):
    def __init__(self, dir):
        super(MetaPickleDict, self).__init__(dir, gzip=False, store_metadata=False, log=False)
        

PickleDir = PickleDict
