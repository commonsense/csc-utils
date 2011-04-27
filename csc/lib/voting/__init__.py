# Import everything from conceptnet.lib.voting for backwards compatibility.
globals().update(dict(__import__('conceptnet.lib.voting', [], [], 'hack').__dict__, __path__=__path__))
