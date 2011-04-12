# Import everything from simplenlp.ar for backwards compatibility.
globals().update(dict(__import__('simplenlp.ar', [], [], 'hack').__dict__, __path__=__path__))
