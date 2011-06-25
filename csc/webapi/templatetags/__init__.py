# Import everything from conceptnet.webapi.templatetags for backwards compatibility.
globals().update(dict(__import__('conceptnet.webapi.templatetags', [], [], 'hack').__dict__, __path__=__path__))
