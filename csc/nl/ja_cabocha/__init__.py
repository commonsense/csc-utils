# Import everything from simplenlp.ja_cabocha for backwards compatibility.
globals().update(dict(__import__('simplenlp.ja_cabocha', [], [], 'hack').__dict__, __path__=__path__))
