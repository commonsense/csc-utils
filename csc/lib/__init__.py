# Import everything from conceptnet.lib for backwards compatibility.
globals().update(dict(__import__('conceptnet.lib', [], [], 'hack').__dict__, __path__=__path__))
