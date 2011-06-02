import random
import os

def write_to_file_atomically(filename, data):
    '''
    Atomically overwrite the file `filename` with the data `data`.

    This should be in the standard library because, though simple, the
    details are subtle. I do not guarantee that even this does it
    correctly.
    '''
    # Choose a random tempfile name because another process may be trying to do the same thing.
    tmp = '%s_tmp_%d' % (filename, random.randrange(1000))
    with open(tmp, 'wb') as f:
        f.write(data)
    os.rename(tmp, filename)
