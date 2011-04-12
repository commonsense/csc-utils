# Import everything from simplenlp.es for backwards compatibility.
globals().update(dict(__import__('simplenlp.es', [], [], 'hack').__dict__, __path__=__path__))
