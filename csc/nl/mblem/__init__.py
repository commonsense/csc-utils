# Import everything from simplenlp.mblem for backwards compatibility.
globals().update(dict(__import__('simplenlp.mblem', [], [], 'hack').__dict__, __path__=__path__))
