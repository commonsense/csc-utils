from __future__ import with_statement
from csc_utils.io import open_for_atomic_overwrite
import os.path
import cPickle as pickle
import base64
import logging
import itertools
from UserDict import DictMixin
LOG = logging.getLogger(__name__)

def unpickle(f):
    if isinstance(f, basestring): f = open(f, 'rb')
    return pickle.load(f)

def save_pickle(obj, filename):
    with open_for_atomic_overwrite(filename) as f:
        pickle.dump(obj, f, -1)
        return f.tell()

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
        LOG.info('Loading %s', name)
        result = unpickle(f)
        f.close()
    except IOError:
        if func is None: raise
        LOG.info('Computing %s', name)
        result = func()
        LOG.info('Saving %s', name)
        save_pickle(result, filename)
    return result
load_pickle = get_picklecached_thing

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


class PickleDict(object, DictMixin):
    '''
    A PickleDict is a dict that dumps its values as pickles in a
    directory. It makes a convenient dumping ground for temporary
    data.

    >>> import tempfile
    >>> dirname = tempfile.mkdtemp()
    >>> pd = PickleDict(dirname, extension='.pkl')

    Let's clear out the directory so the tests start from a known state.
    
    >>> pd._clear()

    >>> pd['abc'] = 123
    >>> pd['abc']
    123

    It keeps an internal cache, so to make sure it's actually storing
    persistently, let's make a new one.

    >>> pd = PickleDict(dirname, extension='.pkl')
    >>> pd['abc']
    123

    It behaves like a dictionary:

    >>> pd.keys()
    ['abc']
    >>> pd.items()
    [('abc', 123)]
    >>> 'abc' in pd
    True
    >>> '' in pd
    False
    >>> 'blue' in pd
    False

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

    ...and delete subdirectories also:

    >>> del pd['dir2']
    >>> 'dir2' in pd
    False

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
    __slots__ = ['logger', 'log', 'dir', 'store_metadata', 'cache', 'extension', 'load_pickle', 'save_pickle']
    
    def __init__(self, dir, store_metadata=True, log=True, extension='', load_pickle=load_pickle, save_pickle=save_pickle):
        self.logger = logging.getLogger('csc_utils.persist.PickleDict')
        self.log = log
        self.dir = os.path.abspath(os.path.expanduser(dir))
        self.extension = extension
        self.store_metadata = store_metadata
        self.load_pickle = load_pickle
        self.save_pickle = save_pickle
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
                if self.extension and filename.endswith(self.extension):
                    filename = filename[:-len(self.extension)]
                if self.key_for_path(filename) == key:
                    key = filename
                    break
            else:
                # Didn't break out of the loop, so key wasn't found. Make a new one.
                key = self.special_character+base64.urlsafe_b64encode(pickle.dumps(key, -1))
        return os.path.join(self.dir, key)

    def key_for_path(self, path):
        if self.extension and path.endswith(self.extension):
            path = path[:-len(self.extension)]
        if path.startswith(self.special_character):
            return pickle.loads(base64.urlsafe_b64decode(path[1:]))
        return path

    def clear_cache(self):
        self.cache = {}

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
            return PickleDict(path, store_metadata=self.store_metadata,
                              extension=self.extension,
                              load_pickle=self.load_pickle,
                              save_pickle=self.save_pickle)
        # Otherwise, expect an actual pickle object, so use the extension.
        path = path + self.extension
        if not os.path.exists(path):
            raise KeyError(key)
        if self.log: self.logger.info('Loading %r...', key)
        data = self.load_pickle(path)
        if self.log: self.logger.info('Loaded %r (%s).', key, type(data))
        return data
        
        
    def __getitem__(self, key):
        if key in self.cache:
            return self.cache[key]
        else:
            data = self._load(key)
            if not isinstance(data, MetaPickleDict): self.cache[key] = data
            return data
    
    def __setitem__(self, key, val):
        if self.log: self.logger.info('Saving %r... (%s)', key, type(val))
        self.cache[key] = val
        size = self.save_pickle(val, self.path_for_key(key) + self.extension)
        if self.log:
            if isinstance(size, int):
                self.logger.info('Saved %r (%s)', key, human_readable_size(size))
            else:
                self.logger.info('Saved %r', key)

        if self.store_metadata:
            meta = {}
            meta['type'] = str(type(val))
            self['_meta'][key] = meta

    def __delitem__(self, key):
        path = self.path_for_key(key)
        if os.path.isdir(path):
            self[key]._clear()
            remaining = os.listdir(path)
            if remaining:
                raise RuntimeError(
                    "PickleDict was trying to delete the subdirectory %s, but "
                    "it still has the following files in it: %r"
                    % (path, remaining))
            else:
                os.rmdir(path)
        else:
            os.remove(path + self.extension)
        self.cache.pop(key, None) # don't fail if it's not cached.
        
    def _clear(self):
        '''
        Clear everything in the directory.
        '''
        for key in self:
            del self[key]
        if '_meta' in self:
            del self['_meta']
    
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
        old_path = self.path_for_key(old)
        new_path = self.path_for_key(new)
        if not os.path.isdir(old_path):
            old_path = old_path + self.extension
            new_path = new_path + self.extension
        os.rename(old_path, new_path)

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
        if key == '':
            return False # Otherwise would match the directory itself.
        if self.store_metadata and key == '_meta':
            return True
        path = self.path_for_key(key)
        return os.path.exists(path) or os.path.exists(path+self.extension)

    def get_meta(self, key, meta_key, default_value=None):
        try:
            return self['_meta'][key][meta_key]
        except KeyError:
            return default_value

    def set_meta(self, key, meta_key, value):
        if not self.store_metadata: return
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
            try:
                return self[key]
            except:
                if self.log: self.logger.warn("Error loading %r; recomputing.", key)

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
            f.key = key
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
        super(MetaPickleDict, self).__init__(dir, store_metadata=False, log=False)
        

###
### PickleClass
###
class PickleClass(object):
    '''A class with lazy members that store their results in a PickleDict.

    Use this class carefully. Lazy results are never automatically recomputed.

    To define a member as lazy, use the Lazy descriptor:

    >>> import tempfile
    >>> dirname = tempfile.mkdtemp()
    >>> class Model(PickleClass):
    ...     @lazy
    ...     def answer(self):
    ...         print 'Called'
    ...         return 42
    ...     @lazy
    ...     def answers(self):
    ...         return (self.answer, self.answer)
    >>> m = Model(dirname)
    >>> m.answers
    Called
    (42, 42)
    >>> m.answer
    42

    "deleting" the attribute deletes the stored value, causing it to be recomputed on next access:

    >>> del m.answer
    >>> m.answer
    Called
    42
    '''
    def __init__(self, path):
        self._pd = PickleDict(path, store_metadata=False)

class lazy(object):
    '''A lazy method descriptor. Think of it as replacing ``@property``.

    For more documentation, see PickleClass.
    '''
    def __init__(self, method, *a, **kw):
        import inspect
        if a or kw or not inspect.isfunction(method):
            self.args = [method]+args
            self.kwargs = kw
            self.method = None
        else:
            self.args = []
            self.kwargs = {}
            self.method = method

    def __call__(self, method):
        assert self.method is None
        self.method = method

    def get_lazy_thunk(self, instance):
        from functools import wraps
        @instance._pd.lazy(*self.args, **self.kwargs)
        @wraps(self.method)
        def lazy_thunk():
            return self.method(instance)
        return lazy_thunk

    def __get__(self, instance, owner):
        if instance is None: raise AttributeError("Needs an instance.")
        return self.get_lazy_thunk(instance)()

    def __delete__(self, instance):
        del instance._pd[self.get_lazy_thunk(instance).key]

