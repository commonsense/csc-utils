# Import everything from simplenlp.fr for backwards compatibility.
globals().update(dict(__import__('simplenlp.fr', [], [], 'hack').__dict__, __path__=__path__))
