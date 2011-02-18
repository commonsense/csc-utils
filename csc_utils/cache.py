from functools import wraps
class cached(object):
    '''Decorator to cache the results of a function depending on its parameters.'''
    def __init__(self, keyname, timeout=60):
        '''keyname_func: called with the same parameters as the wrapped function.
        returns a string containing the key.
        timeout: number of seconds to keep the result in the cache.'''
        if not callable(keyname):
            self.keyname_func = lambda *a: keyname % a
        else:
            self.keyname_func = keyname
        self.timeout = timeout

    def __call__(self, func):
        @wraps(func)
        def wrap(*a, **kw):
            from django.core.cache import cache
            from django.utils.http import urlquote
            
            # Compute the cache key.
            key = urlquote(self.keyname_func(*a, **kw))
            # Try to get it.
            result = cache.get(key)
            if result is not None:
                return result

            # Doesn't exist in the cache.
            result = func(*a, **kw)
            cache.set(key, result, self.timeout)
            return result
        wrap.is_cached = self.is_cached
        wrap.invalidate = self.invalidate
        return wrap

    def is_cached(self, *a, **kw):
        from django.core.cache import cache
        key = self.keyname_func(*a, **kw)
        return cache.get(key) is not None

    def invalidate(self, *a, **kw):
        from django.core.cache import cache
        key = self.keyname_func(*a, **kw)
        cache.delete(key)

    # Times
    minute = 60
    hour = minute*60
    day = hour*24
    week = day*7
    month = day*30
    year = day*365
