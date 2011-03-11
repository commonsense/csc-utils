# Import everything from divisi2 for backwards compatibility.
globals().update(dict(__import__('divisi2', [], [], 'hack').__dict__, __path__=__path__))
