# Import everything from simplenlp.ja for backwards compatibility.
globals().update(dict(__import__('simplenlp.ja', [], [], 'hack').__dict__, __path__=__path__))
