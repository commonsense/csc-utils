from __future__ import with_statement
import random
import os
from contextlib import contextmanager

@contextmanager
def open_for_atomic_overwrite(filename, binary=True):
    # Choose a random tempfile name because another process may be trying to do the same thing.
    tmp = '%s_tmp_%d' % (filename, random.randrange(1000))
    f = open(tmp, 'wb' if binary else 'w')
    try:
        yield f
    except:
        f.close()
        os.unlink(tmp)
        raise
    f.close()
    os.rename(tmp, filename)

def write_to_file_atomically(filename, data):
    '''
    Atomically overwrite the file `filename` with the data `data`.

    This should be in the standard library because, though simple, the
    details are subtle. I do not guarantee that even this does it
    correctly.
    '''
    with open_for_atomic_overwrite(filename) as f:
        f.write(data)
