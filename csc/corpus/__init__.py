import os
import conceptnet.corpus
__path__ = [os.path.dirname(conceptnet.corpus.__file__)]
globals().update(conceptnet.corpus.__dict__)

