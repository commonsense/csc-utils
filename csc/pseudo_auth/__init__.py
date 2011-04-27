# Import everything from conceptnet.pseudo_auth for backwards compatibility.
globals().update(dict(__import__('conceptnet.pseudo_auth', [], [], 'hack').__dict__, __path__=__path__))
