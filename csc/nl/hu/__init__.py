# Import everything from simplenlp.hu for backwards compatibility.
globals().update(dict(__import__('simplenlp.hu', [], [], 'hack').__dict__, __path__=__path__))
