# Import everything from simplenlp.it for backwards compatibility.
globals().update(dict(__import__('simplenlp.it', [], [], 'hack').__dict__, __path__=__path__))
