import os
import conceptnet.webapi
__path__ = [os.path.dirname(conceptnet.webapi.__file__)]
globals().update(conceptnet.webapi.__dict__)

