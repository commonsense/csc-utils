# Import everything from simplenlp.zh for backwards compatibility.
globals().update(dict(__import__('simplenlp.zh', [], [], 'hack').__dict__, __path__=__path__))
