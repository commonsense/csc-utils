# Import everything from simplenlp.pt for backwards compatibility.
globals().update(dict(__import__('simplenlp.pt', [], [], 'hack').__dict__, __path__=__path__))
