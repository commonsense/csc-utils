import os
import conceptnet.lib
__path__ = [os.path.dirname(conceptnet.lib.__file__)]
globals().update(conceptnet.lib.__dict__)
