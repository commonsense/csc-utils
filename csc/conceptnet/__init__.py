# Import everything from conceptnet for backwards compatibility.
globals().update(dict(__import__('conceptnet', [], [], 'hack').__dict__, __path__=__path__))
