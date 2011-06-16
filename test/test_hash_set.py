from nose.tools import *
from csc_utils.ordered_set import HashSet

def test_items():
    hset = HashSet(2)
    eq_(len(hset), 4)

    indices_when_adding = [hset.add(i) for i in range(10)]
    eq_(len(hset), 4)

    items = sorted(hset.items())
    eq_(len(items), 10)
    expected_items = list(enumerate(indices_when_adding))
    eq_(items, expected_items)

def test_entries_with_index():
    N = 1000
    hset = HashSet(1)
    entries_in_bucket_0 = []
    entries_in_bucket_1 = []
    for i in xrange(N):
        bucket = hset.add(i)
        if bucket == 0:
            entries_in_bucket_0.append(i)
        else:
            eq_(bucket, 1)
            entries_in_bucket_1.append(i)
    assert len(entries_in_bucket_0) > N/4
    assert len(entries_in_bucket_1) > N/4
    eq_(len(entries_in_bucket_0) + len(entries_in_bucket_1), N)

    eq_(sorted(hset.entries_with_index(0)), entries_in_bucket_0)
    eq_(sorted(hset.entries_with_index(1)), entries_in_bucket_1)

def test_index():
    hset = HashSet(2)
    N = 1000
    for i in xrange(N):
        hset.add(i)
    for i in xrange(N):
        assert i in hset.entries_with_index(hset.index(i))

def test_contains():
    hset = HashSet(2)
    N = 100
    for i in xrange(N):
        hset.add(i)
    for i in xrange(N):
        assert i in hset
    for i in xrange(N+1, 2*N):
        assert i not in hset

@raises(KeyError)
def test_index_nonpresent():
    hset = HashSet(2)
    hset.index(0)

@raises(ValueError)
def test_bad_shape():
    HashSet(-1)
