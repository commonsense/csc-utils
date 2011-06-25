# Import everything from conceptnet.webapi for backwards compatibility.
globals().update(dict(__import__('conceptnet.webapi', [], [], 'hack').__dict__, __path__=__path__))
