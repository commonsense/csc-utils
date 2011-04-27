# Import everything from conceptnet.network for backwards compatibility.
globals().update(__import__('conceptnet.network', [], [], 'hack').__dict__)
