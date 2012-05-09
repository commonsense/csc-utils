"""
Denormalization
===============

Concepts are often stored in Divisi tensors in a normalized form,
which is often not human-friendly. The ``denormalize`` callback
provides a way "undo" the normalization as concepts are returned. A
denormalizer for ConceptNet concepts is provided, which returns the
"canonical name" of concepts.

File formats
============

Binary format
-------------

The binary format is newer and faster. It consists of a header and a
body (everything is stored in big-endian (network) byte order):

Header:
 * 4 bytes: number of dimensions (integer)
 * 4 bytes: number of items (integer)

The body is a sequence of items with no separator. Each item has a
coordinate for each dimension. Each coordinate is an IEEE float
(32-bit) in big-endian order.

TSV format
----------

The old TSV format is easier to edit by hand or with simple
scripts. Each line is a sequence of fields separated by tabs. The
first field on each line is the concept name. It is followed by a
floating point number for each dimension.

"""

def cnet5_denormalize(concept_text):
    '''
    Returns the canonical denormalized (user-visible) form of a
    concept, given its normalized text of a concept.
    '''
    parts = concept_text.split('/')
    lang = parts[2]
    if len(parts) > 4:
        result = "/".join(parts[3:5])
    elif len(parts) > 3:
        result = parts[3]
    else:
        # might not be ConceptNet at all
        return concept_text

    if lang != 'en':
        return '%s [%s]' % (result, lang)
    else: return result

def null_denormalize(x): return x

def write_packed(matrix, labels, out_basename, denormalize=None, cutoff=40):
    '''
    Export in the new binary coordinate file format.
    '''

    import struct
    names = open(out_basename+'.names','wb')
    coords = open(out_basename+'.coords', 'wb')

    if denormalize is None:
        denormalize = null_denormalize

    num_vecs, num_dims = matrix.shape
    if num_dims > cutoff: num_dims = cutoff
    coords.write(struct.pack('>ii', num_dims, num_vecs))

    # Write the whole file.
    format_str = '>' + 'f'*num_dims
    for row in xrange(len(labels)):
        concept = denormalize(labels[row])
        vec = matrix[row, :]
        coords.write(struct.pack(format_str, *vec[:cutoff]))
        names.write(concept+'\n')

    names.close()
    coords.close()

