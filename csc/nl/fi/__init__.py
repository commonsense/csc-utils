# Import everything from simplenlp.fi for backwards compatibility.
globals().update(dict(__import__('simplenlp.fi', [], [], 'hack').__dict__, __path__=__path__))
