# Import everything from conceptnet.lib.events for backwards compatibility.
globals().update(dict(__import__('conceptnet.lib.events', [], [], 'hack').__dict__, __path__=__path__))
