# Import everything from simplenlp.en for backwards compatibility.
globals().update(dict(__import__('simplenlp.en', [], [], 'hack').__dict__, __path__=__path__))
