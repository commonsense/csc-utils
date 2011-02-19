import os
import conceptnet
__path__ = [os.path.dirname(__file__), os.path.dirname(conceptnet.__file__)]
mypath = __path__
globals().update(conceptnet.__dict__)
__path__ = mypath
