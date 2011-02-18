import os
import conceptnet.pseudo_auth
__path__ = [os.path.dirname(conceptnet.pseudo_auth.__file__)]
globals().update(conceptnet.pseudo_auth.__dict__)

