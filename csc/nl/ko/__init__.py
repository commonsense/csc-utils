# Import everything from simplenlp.ko for backwards compatibility.
globals().update(dict(__import__('simplenlp.ko', [], [], 'hack').__dict__, __path__=__path__))
