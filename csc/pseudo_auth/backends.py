# Import everything from conceptnet.pseudo_auth.backends for backwards compatibility.
globals().update(__import__('conceptnet.pseudo_auth.backends', [], [], 'hack').__dict__)
