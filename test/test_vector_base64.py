from csc.util.vector import pack64, unpack64
import numpy as np
import random

def random_vector():
    vec = np.random.normal(size=(random.randrange(0, 20)))\
      * (2 ** np.random.normal(0, 10))
    return np.minimum(2.0**39, np.maximum(-2.0**39, vec))

def test_round_trip():
    for i in range(1000):
        vec = random_vector()
        out = unpack64(pack64(vec))
        err = (vec-out)

        assert (np.linalg.norm(err) < 1e-9 or
                np.linalg.norm(err)/np.linalg.norm(vec) < 1e-4)

