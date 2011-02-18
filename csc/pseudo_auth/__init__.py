import os
import conceptnet
__path__ = [os.path.dirname(conceptnet.pseudo_auth.__file__)]
globals().update(conceptnet.pseudo_auth.__dict__)

