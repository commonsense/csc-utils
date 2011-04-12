# Import everything from simplenlp for backwards compatibility.
globals().update(dict(__import__('simplenlp', [], [], 'hack').__dict__, __path__=__path__))
