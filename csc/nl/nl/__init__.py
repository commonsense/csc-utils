# Import everything from simplenlp.nl for backwards compatibility.
globals().update(dict(__import__('simplenlp.nl', [], [], 'hack').__dict__, __path__=__path__))
