# Import everything from conceptnet.corpus for backwards compatibility.
globals().update(dict(__import__('conceptnet.corpus', [], [], 'hack').__dict__, __path__=__path__))
