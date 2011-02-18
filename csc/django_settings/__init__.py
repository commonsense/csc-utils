import os
import conceptnet
__path__ = [os.path.dirname(conceptnet.django_settings.__file__)]
globals().update(conceptnet.django_settings.__dict__)

