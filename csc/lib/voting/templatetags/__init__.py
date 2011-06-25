# Import everything from conceptnet.lib.voting.templatetags for backwards compatibility.
globals().update(dict(__import__('conceptnet.lib.voting.templatetags', [], [], 'hack').__dict__, __path__=__path__))
